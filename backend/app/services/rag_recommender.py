"""
RAG (Retrieval-Augmented Generation) based recommendation engine
Uses sentence transformers for embeddings and ChromaDB for vector search
"""
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from app.models.schemas import RecommendationRequest, RecommendationItem, RecommendationScore, AssessmentResponse
from app.core.config import get_settings
from app.core.logging import log

settings = get_settings()


class RAGRecommender:
    """
    RAG-based recommendation engine using semantic search
    """
    
    def __init__(self):
        """Initialize RAG recommender with lazy loading"""
        self.model_name = settings.embedding_model
        self.dimension = settings.vector_dimension
        self.top_k = settings.top_k_results
        
        # Lazy loading flags
        self._embedding_model = None
        self._chroma_client = None
        self._collection = None
        self._indexed = False
        
        log.info(f"RAG recommender initialized (lazy loading mode)")
    
    def _ensure_model_loaded(self):
        """Lazy load embedding model with timeout protection"""
        if self._embedding_model is not None:
            return
        
        import signal
        from contextlib import contextmanager
        
        @contextmanager
        def timeout(seconds):
            """Context manager for timeout"""
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Model loading exceeded {seconds} seconds")
            
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        try:
            log.info(f"Loading embedding model: {self.model_name}")
            timeout_seconds = getattr(settings, 'model_loading_timeout', 60)
            
            # Try with timeout on Unix systems
            try:
                with timeout(timeout_seconds):
                    self._embedding_model = SentenceTransformer(self.model_name)
            except (AttributeError, ValueError):
                # Windows doesn't support SIGALRM, load without timeout
                log.warning("Timeout not supported on this platform, loading without timeout")
                self._embedding_model = SentenceTransformer(self.model_name)
            
            log.info(f"Embedding model loaded successfully")
        except TimeoutError as e:
            log.error(f"Model loading timeout: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")
        except Exception as e:
            log.error(f"Error loading embedding model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    def _ensure_collection_loaded(self):
        """Lazy load ChromaDB collection"""
        if self._collection is not None:
            return
        
        try:
            log.info("Initializing ChromaDB client")
            self._chroma_client = chromadb.Client(Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ))
            
            # Create or get collection
            try:
                self._collection = self._chroma_client.get_collection(name="assessments")
                log.info("Loaded existing ChromaDB collection")
            except:
                self._collection = self._chroma_client.create_collection(
                    name="assessments",
                    metadata={"hnsw:space": "cosine"}
                )
                log.info("Created new ChromaDB collection")
        except Exception as e:
            log.error(f"Error initializing ChromaDB: {e}")
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
    
    def _create_assessment_text(self, assessment: dict) -> str:
        """Create rich text representation of assessment"""
        parts = [
            f"Assessment: {assessment.get('name', '')}",
            f"Type: {assessment.get('type', '')}",
        ]
        
        if assessment.get('job_family', ''):
            parts.append(f"Job Family: {assessment.get('job_family', '')}")
        
        if assessment.get('job_level', ''):
            parts.append(f"Job Level: {assessment.get('job_level', '')}")
        
        if assessment.get('description', ''):
            parts.append(f"Description: {assessment.get('description', '')}")
        
        # Add test types
        test_types = []
        if test_types:
            parts.append(f"Test Types: {', '.join(test_types)}")
        
        # Add skills
        skills = []
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Add industries
        industries = []
        if industries:
            parts.append(f"Industries: {', '.join(industries)}")
        
        return " | ".join(parts)
    
    def index_assessments(self, db):
        """Index all assessments in ChromaDB with memory optimization"""
        import gc
        
        # Ensure model and collection are loaded
        self._ensure_model_loaded()
        self._ensure_collection_loaded()
        
        if self._indexed:
            log.info("Assessments already indexed, skipping")
            return
        
        log.info("Starting assessment indexing for RAG")
        
        response = db.table("assessments").select("*").execute()
        assessments = response.data
        
        if not assessments:
            log.warning("No assessments found to index")
            return
        
        # Helper to create batches
        def batch_data(data, batch_size):
            for i in range(0, len(data), batch_size):
                yield data[i:i + batch_size]
        
        total_indexed = 0
        batch_size = 32  # Small batch size for 512MB RAM
        
        # Process in batches
        for batch_idx, batch_assessments in enumerate(batch_data(assessments, batch_size)):
            try:
                documents = []
                metadatas = []
                ids = []
                
                for assessment in batch_assessments:
                    text = self._create_assessment_text(assessment)
                    documents.append(text)
                    
                    # Create metadata
                    metadata = {
                        "id": assessment['id'],
                        "name": assessment.get('name', ''),
                        "type": assessment.get('type', ''),
                        "job_family": assessment.get('job_family', '') or "",
                        "job_level": assessment.get('job_level', '') or "",
                        "remote_testing": str(assessment.get('remote_testing', False)),
                        "duration": str(assessment.get('duration', 0) or 0)
                    }
                    metadatas.append(metadata)
                    ids.append(assessment['id'])
                
                # Generate embeddings for batch
                embeddings = self._embedding_model.encode(documents, show_progress_bar=False)
                
                # Add to ChromaDB
                self._collection.add(
                    embeddings=embeddings.tolist(),
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_indexed += len(batch_assessments)
                log.info(f"Indexed batch {batch_idx + 1} ({len(batch_assessments)} items)")
                
                # Explicit cleanup
                del documents, metadatas, ids, embeddings
                gc.collect()
                
            except Exception as e:
                log.error(f"Error indexing batch {batch_idx}: {e}")
                continue
        
        self._indexed = True
        log.info(f"Successfully indexed {total_indexed} assessments")
        gc.collect()
    
    def _create_query_text(self, request: RecommendationRequest) -> str:
        """Create query text from request"""
        parts = []
        
        if request.job_title:
            parts.append(f"Job Title: {request.job_title}")
        
        if request.job_family:
            parts.append(f"Job Family: {request.job_family}")
        
        if request.job_level:
            parts.append(f"Job Level: {request.job_level}")
        
        if request.industry:
            parts.append(f"Industry: {request.industry}")
        
        if request.required_skills:
            parts.append(f"Skills: {', '.join(request.required_skills)}")
        
        if request.test_types:
            test_type_strs = [tt.value if hasattr(tt, 'value') else tt for tt in request.test_types]
            parts.append(f"Test Types: {', '.join(test_type_strs)}")
        
        query = " | ".join(parts) if parts else "General assessment recommendation"
        return query
    
    async def recommend(
        self, 
        request: RecommendationRequest, 
        db
    ) -> List[RecommendationItem]:
        """
        Generate recommendations using RAG
        
        Args:
            request: Recommendation request
            db: Database session
            
        Returns:
            List of recommendation items
        """
        # Ensure model and collection are loaded
        self._ensure_model_loaded()
        self._ensure_collection_loaded()
        
        # Index assessments if not already done
        if not self._indexed:
            log.info("Indexing assessments on first use")
            self.index_assessments(db)
        
        log.info(f"RAG recommendation for: {request.dict()}")
        
        # Create query
        query_text = self._create_query_text(request)
        log.info(f"Query text: {query_text}")
        
        # Generate query embedding
        query_embedding = self._embedding_model.encode([query_text])[0]
        
        # Search in ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(request.num_recommendations * 2, 20),
            include=["distances", "metadatas", "documents"]
        )
        
        if not results['ids'] or not results['ids'][0]:
            log.warning("No results found from ChromaDB")
            return []
        
        # Process results
        recommendations = []
        
        for idx, (assessment_id, distance, metadata) in enumerate(zip(
            results['ids'][0],
            results['distances'][0],
            results['metadatas'][0]
        )):
            # Get full assessment from database
            response = db.table("assessments").select("*").eq("id", assessment_id).execute()
            assessment = response.data[0] if response.data else None
            
            if not assessment:
                continue
            
            # Apply filters
            if request.remote_testing_required and not assessment.get('remote_testing', False):
                continue
            
            if request.max_duration and assessment.get('duration', 0) and assessment.get('duration', 0) > request.max_duration:
                continue
            
            if request.language:
                languages = ['English']
                if request.language not in languages:
                    continue
            
            # Calculate scores (distance is 0-2, we convert to similarity 0-1)
            similarity = max(0, 1 - (distance / 2))
            relevance_score = similarity
            
            # Create response
            assessment_response = self._db_to_response(assessment)
            
            score = RecommendationScore(
                total_score=relevance_score,
                relevance_score=relevance_score,
                confidence=similarity,
                explanation=f"Semantic similarity: {similarity:.2f}"
            )
            
            recommendations.append(RecommendationItem(
                assessment=assessment_response,
                score=score,
                rank=idx + 1
            ))
            
            if len(recommendations) >= request.num_recommendations:
                break
        
        log.info(f"RAG returned {len(recommendations)} recommendations")
        return recommendations
    
    def _db_to_response(self, assessment: dict) -> AssessmentResponse:
        """Convert database model to response schema"""
        return AssessmentResponse(
            id=assessment['id'],
            name=assessment.get('name', 'Unknown Assessment'),
            type=assessment.get('type', 'Assessment'),
            test_types=assessment.get('test_types', []) if isinstance(assessment.get('test_types'), list) else [],
            remote_testing=assessment.get('remote_testing', False),
            adaptive=assessment.get('adaptive', False),
            job_family=assessment.get('job_family') or None,
            job_level=assessment.get('job_level') or None,
            industries=assessment.get('industries', []) if isinstance(assessment.get('industries'), list) else [],
            languages=assessment.get('languages', ['English']) if isinstance(assessment.get('languages'), list) else ['English'],
            skills=assessment.get('skills', []) if isinstance(assessment.get('skills'), list) else [],
            description=assessment.get('description', ''),
            duration=assessment.get('duration') or None
        )


