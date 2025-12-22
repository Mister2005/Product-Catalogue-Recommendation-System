"""
Updated RAG Recommender with Supabase pgvector Support
Supports both ChromaDB (local) and Supabase (production)
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.services.embedding_service import HuggingFaceEmbeddingService
from app.core.vector_db import get_vector_db
# CrossEncoder imported conditionally in __init__ for development only
import os
import google.generativeai as genai
import json
import numpy as np
from rank_bm25 import BM25Okapi
from collections import defaultdict
import requests

log = logging.getLogger(__name__)

class RAGRecommender:
    """
    RAG-based recommendation engine with hybrid backend support.
    
    Supports:
    - ChromaDB (local development)
    - Supabase pgvector (production)
    
    Features:
    - Cross-Encoder Reranking
    - Gemini-based Query Expansion
    - BM25 Keyword Search
    - Metadata Filtering
    """
    def __init__(self):
        self.embedding_service = HuggingFaceEmbeddingService()
        
        # Load Config
        model_name = os.getenv("RERANKING_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.retrieval_k = int(os.getenv("RAG_RETRIEVAL_COUNT", "50"))
        self.score_threshold = float(os.getenv("RERANKING_SCORE_THRESHOLD", "-2.0"))
        
        # Get vector database backend (non-blocking - allow startup even if DB is slow)
        try:
            self.vector_db = get_vector_db()
            try:
                count = self.vector_db.count()
                log.info(f"Vector DB initialized with {count} assessments")
            except Exception as count_error:
                log.warning(f"Could not get vector DB count: {count_error}")
                log.warning("Vector DB may be slow or empty. Recommendations will work once DB is ready.")
        except Exception as e:
            log.error(f"Failed to initialize vector DB: {e}")
            log.error("Recommendations will fail until vector DB is properly configured.")
            # Don't raise - allow app to start anyway
            self.vector_db = None
        
        # Load URL mapping
        base_dir = Path(__file__).parent.parent.parent
        mapping_path = base_dir.parent / "url_mapping.json"
        self.url_mapping = {}
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                # Direct mapping: old_url -> new_url
                self.url_mapping = json.load(f)
            log.info(f"Loaded URL mapping with {len(self.url_mapping)} entries")
        
        # Gemini setup
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.gemini_model = genai.GenerativeModel(model_id) 
            log.info(f"Gemini Client initialized with model: {model_id}")
        else:
            self.gemini_model = None
            log.warning("GEMINI_API_KEY not found. Query Expansion disabled.")

        log.info(f"Initializing Reranker: {model_name}")
        self.reranker_api_url = os.getenv("RERANKER_API_URL")
        
        # CRITICAL: Never load local CrossEncoder in production (causes OOM on Render)
        # Only use remote API or skip reranking
        environment = os.getenv("ENVIRONMENT", "development")
        
        if self.reranker_api_url:
            log.info(f"Using Remote Reranker API: {self.reranker_api_url}")
            self.reranker = "REMOTE"
        elif environment == "production":
            # In production without API, skip reranking to avoid OOM
            log.warning("No RERANKER_API_URL in production. Reranking disabled to prevent OOM.")
            self.reranker = None
        else:
            try:
                # Only load local model in development
                log.info("Development mode: Loading local CrossEncoder...")
                from sentence_transformers import CrossEncoder
                self.reranker = CrossEncoder(model_name)
                log.info(f"Loaded Local Reranker: {model_name}")
            except Exception as e:
                log.error(f"Failed to load Reranker: {e}")
                self.reranker = None

        # BM25 Index - Lazy load to save memory
        self.bm25 = None
        self.bm25_docs = []
        self.bm25_metas = []
        self._bm25_initialized = False
        log.info("BM25 index will be lazy-loaded on first use")
    
    def _ensure_bm25_initialized(self):
        """Lazy-load BM25 index on first use"""
        if self._bm25_initialized:
            return
            
        try:
            # Get all documents from vector DB
            metadatas, documents = self.vector_db.get_all()
            
            self.bm25_docs = documents
            self.bm25_metas = metadatas
            
            # Tokenize documents for BM25
            tokenized_docs = [doc.lower().split() for doc in self.bm25_docs]
            self.bm25 = BM25Okapi(tokenized_docs)
            
            self._bm25_initialized = True
            log.info(f"Built BM25 index with {len(self.bm25_docs)} documents")
        except Exception as e:
            log.error(f"Failed to build BM25 index: {e}")
            self.bm25 = None
            self.bm25_docs = []
            self.bm25_metas = []

    def extract_metadata_constraints(self, user_query: str) -> Dict[str, Any]:
        """Extract metadata constraints from query using Gemini"""
        if not self.gemini_model:
            return {}
        
        try:
            prompt = (
                f"Extract assessment constraints from this query: '{user_query}'\n\n"
                f"Return ONLY valid JSON with these fields (use null if not mentioned):\n"
                f"{{"
                f'  "max_duration_minutes": <int or null>,\n'
                f'  "requires_remote": <true/false/null>,\n'
                f'  "requires_adaptive": <true/false/null>,\n'
                f'  "job_level": <"Entry_Level" | "Manager_Senior" | "General">\n'
                f"}}\n\n"
                f"Examples:\n"
                f"- '1 hour assessment' -> {{\"max_duration_minutes\": 60}}\n"
                f"- 'remote testing' -> {{\"requires_remote\": true}}\n"
                f"- 'adaptive test' -> {{\"requires_adaptive\": true}}\n"
                f"- 'hiring interns' -> {{\"job_level\": \"Entry_Level\"}}\n"
                f"- 'senior manager role' -> {{\"job_level\": \"Manager_Senior\"}}"
            )
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            if '{' in text:
                json_start = text.index('{')
                json_end = text.rindex('}') + 1
                json_str = text[json_start:json_end]
                constraints = json.loads(json_str)
                log.info(f"Extracted constraints: {constraints}")
                return constraints
            return {}
        except Exception as e:
            log.error(f"Metadata extraction failed: {e}")
            return {}
    
    def multi_expand_query(self, user_query: str) -> List[str]:
        """
        Generates multiple diverse search queries for better coverage.
        Returns: [original_query, skills_query, roles_query, domain_query]
        """
        # ALWAYS include the original query first for exact matching
        queries = [user_query]
        
        if not self.gemini_model:
            return queries
            
        try:
            prompt = (
                f"Generate 3 different search queries for finding assessments for: '{user_query}'\n\n"
                f"1. SKILLS: Extract technical skills, competencies, and abilities needed\n"
                f"2. ROLES: Job title synonyms, related positions, and career levels\n"
                f"3. DOMAIN: Industry terms, business context, and domain knowledge\n\n"
                f"Output format (one per line):\n"
                f"SKILLS: <comma-separated keywords>\n"
                f"ROLES: <comma-separated keywords>\n"
                f"DOMAIN: <comma-separated keywords>\n\n"
                f"Keep each line concise (max 10 keywords)."
            )
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse the three variants
            expanded_queries = []
            for line in text.split('\n'):
                if ':' in line:
                    _, keywords = line.split(':', 1)
                    expanded_queries.append(keywords.strip())
            
            # Add expanded queries to the list
            if len(expanded_queries) >= 3:
                queries.extend(expanded_queries[:3])
            else:
                # Fallback: duplicate original query
                queries.extend([user_query] * 3)
            
            log.info(f"Multi-Query Expansion: {len(queries)} variants (original + {len(queries)-1} expanded)")
            return queries[:4]  # Return original + 3 expanded = 4 total
            
        except Exception as e:
            log.error(f"Multi-Query Expansion failed: {e}")
            return queries  # Return at least the original query

    def recommend(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid Retrieval: Multi-Query + BM25 + Semantic + Metadata Filtering + Reranking
        """
        try:
            # Safety check: if vector DB failed to initialize, return empty
            if not self.vector_db:
                log.error("Vector DB not initialized. Cannot provide recommendations.")
                return []
            
            # 0. Extract Metadata Constraints
            constraints = self.extract_metadata_constraints(query)
            
            # 1. Multi-Query Expansion
            search_queries = self.multi_expand_query(query)
            
            # 1.5. Exact Name Matching Layer (New)
            # Ensure assessments with names matching query terms are included candidates
            # This fixes the "Retrieval Gap" where correct named items weren't being retrieved
            
            all_candidates = {}
            all_docs = {}
            
            # Targeted keywords that justify single-word matching
            TARGET_KEYWORDS = {
                'verbal', 'numerical', 'logical', 'personality', 'cognitive', 'aptitude',
                'java', 'python', 'sql', 'tableau', 'react', 'angular', 'node', 'marketing', 'sales',
                'finance', 'account', 'manager', 'english', 'communication'
            }
            
            # Lazy-load BM25 index if needed
            self._ensure_bm25_initialized()
            
            if self.bm25_metas:
                query_lower = query.lower()
                query_parts = set(query_lower.split())
                
                match_count = 0
                for idx, meta in enumerate(self.bm25_metas):
                    url = meta.get('url')
                    name = meta.get('name', '').lower()
                    
                    if not name or not url:
                        continue
                        
                    # Check for name matches
                    is_match = False
                    
                    # 1. Exact phrase match in query
                    if name in query_lower and len(name) > 3: 
                        is_match = True
                    
                    # 2. Keyword overlap
                    else:
                        name_parts = set(name.split())
                        if name_parts:
                            overlap = len(query_parts.intersection(name_parts))
                            
                            # A) Targeted Single-Keyword Match
                            # if matched word is high-value (e.g. "verbal"), include it
                            common_words = query_parts.intersection(name_parts)
                            if any(w in TARGET_KEYWORDS for w in common_words):
                                is_match = True
                            
                            # B) Robust Name Match (Standard)
                            # Short names (<= 2 words): 1 match enough
                            elif len(name_parts) <= 2 and overlap >= 1:
                                is_match = True
                            # Long names: 50% coverage or at least 2 words
                            elif overlap >= len(name_parts) / 2:
                                is_match = True
                            elif overlap >= 2:
                                is_match = True
                    
                    if is_match:
                         if url not in all_candidates:
                             all_candidates[url] = meta
                             all_docs[url] = self.bm25_docs[idx]
                             match_count += 1
                
                log.info(f"Exact Name Matching candidates: {match_count}")
            
            # Start Semantic Search loop
            for idx, search_query in enumerate(search_queries):
                # Truncate if needed
                if len(search_query) > 1000:
                    search_query = search_query[:1000]
                
                # A) Semantic Search via Vector DB
                query_embedding = self.embedding_service.encode(search_query, is_query=True).tolist()
                
                # Convert constraints to filter format
                filters = {}
                if constraints.get('job_level'):
                    filters['job_level'] = constraints['job_level']
                if constraints.get('max_duration_minutes'):
                    filters['max_duration'] = constraints['max_duration_minutes']
                if constraints.get('requires_remote'):
                    filters['remote_support'] = 'Yes'
                if constraints.get('requires_adaptive'):
                    filters['adaptive_support'] = 'Yes'
                
                sem_metas, sem_docs = self.vector_db.search(
                    query_embedding=query_embedding,
                    n_results=self.retrieval_k,
                    filters=filters if filters else None
                )
                
                # ✅ Fallback: If no results with job_level filter, retry without it
                if len(sem_metas) == 0 and filters and filters.get('job_level'):
                    log.warning(f"No results with job_level={filters['job_level']} filter. Retrying without job level constraint...")
                    filters_no_level = {k: v for k, v in filters.items() if k != 'job_level'}
                    sem_metas, sem_docs = self.vector_db.search(
                        query_embedding=query_embedding,
                        n_results=self.retrieval_k,
                        filters=filters_no_level if filters_no_level else None
                    )
                
                # Add semantic results
                for meta, doc in zip(sem_metas, sem_docs):
                    url = meta.get('url')
                    if url and url not in all_candidates:
                        all_candidates[url] = meta
                        all_docs[url] = doc
                
                # B) BM25 Keyword Search
                if self.bm25:
                    tokenized_query = search_query.lower().split()
                    bm25_scores = self.bm25.get_scores(tokenized_query)
                    
                    # Get top K indices
                    top_indices = np.argsort(bm25_scores)[-self.retrieval_k:][::-1]
                    
                    for idx_bm25 in top_indices:
                        if idx_bm25 < len(self.bm25_metas):
                            meta = self.bm25_metas[idx_bm25]
                            doc = self.bm25_docs[idx_bm25]
                            url = meta.get('url')
                            
                            # Apply manual filtering for BM25 results
                            if constraints:
                                # Check duration constraint
                                if constraints.get('max_duration_minutes'):
                                    duration = meta.get('duration', 0)
                                    if isinstance(duration, (int, float)) and duration > constraints['max_duration_minutes']:
                                        continue
                                
                                # Check remote constraint
                                if constraints.get('requires_remote') is True:
                                    if meta.get('remote_support', '').lower() != 'yes':
                                        continue

                                # Check job level constraint
                                if constraints.get('job_level') and constraints['job_level'] != 'General':
                                    cand_level = meta.get('job_level', 'General')
                                    req_level = constraints['job_level']
                                    
                                    # Strict filtering for mismatched levels
                                    if req_level == 'Entry_Level' and cand_level == 'Manager_Senior':
                                        continue
                                    if req_level == 'Manager_Senior' and cand_level == 'Entry_Level':
                                        continue
                                
                                # Check adaptive constraint
                                if constraints.get('requires_adaptive') is True:
                                    if meta.get('adaptive_support', '').lower() != 'yes':
                                        continue
                                
                                # REMOVED: Pre-packaged filter to improve recall
                                # We now trust the reranker/query match to prioritize relevant items
                            
                            if url and url not in all_candidates:
                                all_candidates[url] = meta
                                all_docs[url] = doc
            
            # Prepare for reranking
            if not all_candidates:
                return []
            
            metas = list(all_candidates.values())
            docs = list(all_docs.values())
            
            log.info(f"Multi-query + BM25 + Filtering retrieved {len(metas)} unique candidates from {len(search_queries)} queries")
            
            # 3. Reranking Step with Balanced Keyword Boost
            scores = []
            
            if self.reranker and docs:
                rerank_query = query  # Original query
                
                if self.reranker == "REMOTE":
                    # --- REMOTE API PATH ---
                    try:
                        resp = requests.post(
                            f"{self.reranker_api_url}/rerank",  # ✅ Fixed: Add /rerank endpoint
                            json={
                                "query": rerank_query,
                                "documents": docs
                            },
                            timeout=10.0  # Increased timeout for production
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            scores = np.array(data.get("scores", []))
                            if len(scores) == 0:
                                log.warning("Remote Reranker returned empty scores")
                                # Fallback: zero scores
                                scores = np.zeros(len(docs))
                        else:
                            log.error(f"Remote Reranker API failed: {resp.status_code} {resp.text}")
                            scores = np.zeros(len(docs))
                    except Exception as e:
                        log.error(f"Error calling Remote Reranker: {e}")
                        scores = np.zeros(len(docs))
                        
                else:
                    # --- LOCAL MODEL PATH ---
                    pairs = [[rerank_query, doc] for doc in docs]
                    scores = self.reranker.predict(pairs)
                
                # Apply balanced keyword matching boost
                query_keywords = set(rerank_query.lower().split())
                boosted_scores = []
                
                for idx, score in enumerate(scores):
                    # Check for keyword overlap in document
                    doc_text = docs[idx].lower()
                    doc_keywords = set(doc_text.split())
                    
                    # Calculate keyword overlap
                    overlap = len(query_keywords.intersection(doc_keywords))
                    overlap_ratio = overlap / len(query_keywords) if query_keywords else 0
                    
                    # Moderate boost based on keyword overlap (up to +3.0)
                    keyword_boost = overlap_ratio * 3.0
                    
                    # Strong boost for assessment name matching
                    assessment_name = metas[idx].get('name', '').lower()
                    name_keywords = set(assessment_name.split())
                    name_overlap = len(query_keywords.intersection(name_keywords))
                    name_overlap_ratio = name_overlap / len(query_keywords) if query_keywords else 0
                    
                    # Higher boost for name matches (up to +5.0)
                    name_boost = name_overlap_ratio * 5.0
                    
                    # ✅ Apply job level penalty instead of hard filtering
                    job_level_penalty = 0
                    if constraints.get('job_level'):
                        cand_level = metas[idx].get('job_level', 'General')
                        req_level = constraints['job_level']
                        
                        # Strong penalty for mismatched levels
                        if req_level == 'Entry_Level' and cand_level == 'Manager_Senior':
                            job_level_penalty = -3.0
                        elif req_level == 'Manager_Senior' and cand_level == 'Entry_Level':
                            job_level_penalty = -3.0
                        # General level or matching level gets no penalty
                    
                    # Total boost with penalty
                    total_boost = keyword_boost + name_boost + job_level_penalty
                    boosted_score = score + total_boost
                    
                    boosted_scores.append(boosted_score)
                
                # Combine meta, doc, and boosted score
                ranked_candidates = []
                for idx, score in enumerate(boosted_scores):
                    ranked_candidates.append({
                        "meta": metas[idx],
                        "score": score,
                        "original_score": scores[idx],
                        "boost": boosted_scores[idx] - scores[idx]
                    })
                
                # Sort by boosted score descending
                ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
                
                # Filter by score threshold instead of forcing top N
                filtered_results = [
                    x for x in ranked_candidates 
                    if x["score"] >= self.score_threshold
                ]
                
                # Limit to n_results after filtering
                top_results = filtered_results[:n_results]
                
                # Extract metas
                final_metas = [x["meta"] for x in top_results]
                
                if top_results:
                    log.info(f"Reranked {len(docs)} candidates. Filtered to {len(top_results)} above threshold {self.score_threshold}. Top score: {top_results[0]['score']:.3f} (boost: +{top_results[0]['boost']:.3f})")
                else:
                    log.warning(f"No results above threshold {self.score_threshold}")
                
            else:
                # Fallback if no reranker
                final_metas = metas[:n_results]

            # 4. Format Results with URL Remapping
            recommendations = []
            for meta in final_metas:
                source_url = meta.get("url")
                # Remap URL if mapping exists
                final_url = self.url_mapping.get(source_url, source_url)
                
                item = {
                    "url": final_url,
                    "name": meta.get("name"),
                    "adaptive_support": meta.get("adaptive_support", "No"),
                    "description": meta.get("description", ""),
                    "duration": meta.get("duration", 0),
                    "remote_support": meta.get("remote_support", "No"),
                    "test_type": [meta.get("test_type", "General")] 
                }
                recommendations.append(item)
                
            return recommendations
            
        except Exception as e:
            log.error(f"Error during RAG recommendation: {e}")
            import traceback
            log.error(traceback.format_exc())
            return []

    def chat(self, message: str, history: List[Dict[str, str]] = []) -> str:
        """
        Chat with Gemini about SHL assessments.
        """
        try:
            # Construct context from history
            context = (
                "You are an expert SHL Assessment Assistant. help users find the right assessments.\n"
                "Keep responses concise and professional.\n"
            )
            
            if history:
                context += "Previous conversation:\n"
                for msg in history:
                    context += f"{msg['role'].title()}: {msg['content']}\n"
            
            prompt = f"{context}\nUser: {message}\nAssistant:"
            
            # Generate response
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            log.error(f"Error during chat: {e}")
            return "I apologize, but I'm having trouble connecting to the AI service right now. Please try again."
