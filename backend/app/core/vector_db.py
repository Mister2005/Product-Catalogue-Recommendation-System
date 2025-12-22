"""
Vector Database Abstraction Layer
Supports both ChromaDB (local) and Supabase pgvector (cloud)
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class VectorDB(ABC):
    """Abstract base class for vector database operations"""
    
    @abstractmethod
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Tuple of (metadatas, documents)
        """
        pass
    
    @abstractmethod
    def get_all(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Get all documents and metadata
        
        Returns:
            Tuple of (metadatas, documents)
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total number of documents"""
        pass


class ChromaDBBackend(VectorDB):
    """ChromaDB implementation for local development"""
    
    def __init__(self):
        import chromadb
        
        base_dir = Path(__file__).parent.parent.parent
        db_path = base_dir / "data" / "chromadb"
        
        log.info(f"Connecting to ChromaDB at {db_path}")
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Get or create collection
        existing_collections = self.client.list_collections()
        exists = any(c.name == "shl_assessments" for c in existing_collections)
        
        if not exists:
            log.warning("Collection 'shl_assessments' not found. Creating...")
            self.collection = self.client.create_collection(
                "shl_assessments", 
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.collection = self.client.get_collection(name="shl_assessments")
        
        count = self.collection.count()
        if count == 0:
            log.warning("ChromaDB collection is empty. Run ingestion first.")
        else:
            log.info(f"Connected to ChromaDB with {count} items")
    
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Search using ChromaDB"""
        where_filter = None
        if filters:
            # Convert filters to ChromaDB format
            where_filter = {}
            for key, value in filters.items():
                if value is not None:
                    where_filter[key] = value
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        documents = results['documents'][0] if results['documents'] else []
        
        return metadatas, documents
    
    def get_all(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Get all documents from ChromaDB"""
        all_data = self.collection.get(include=["documents", "metadatas"])
        return all_data['metadatas'], all_data['documents']
    
    def count(self) -> int:
        """Get count from ChromaDB"""
        return self.collection.count()


class SupabaseVectorBackend(VectorDB):
    """Supabase pgvector implementation for production"""
    
    def __init__(self):
        from app.core.database import get_supabase_client
        
        self.db = get_supabase_client()
        self.table_name = "assessment_embeddings"
        
        # Verify table exists (non-blocking - just warn if fails)
        try:
            result = self.db.table(self.table_name).select("id").limit(1).execute()
            count = len(result.data) if result.data else 0
            log.info(f"Connected to Supabase pgvector table '{self.table_name}' ({count} sample records)")
        except Exception as e:
            log.warning(f"Could not verify Supabase table '{self.table_name}': {e}")
            log.warning("Table may not exist or connection may be slow. Queries will fail until this is resolved.")
    
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Search using Supabase pgvector
        
        Uses direct SQL query with vector similarity
        """
        try:
            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Build base query with filters
            query_builder = self.db.table(self.table_name).select("*")
            
            # Apply metadata filters
            if filters:
                if filters.get('job_level'):
                    query_builder = query_builder.eq('job_level', filters['job_level'])
                if filters.get('max_duration'):
                    query_builder = query_builder.lte('duration', filters['max_duration'])
                if filters.get('remote_support'):
                    query_builder = query_builder.eq('remote_support', filters['remote_support'])
                if filters.get('adaptive_support'):
                    query_builder = query_builder.eq('adaptive_support', filters['adaptive_support'])
            
            # For now, get all filtered results and sort in Python
            # This is a workaround since the Supabase Python client doesn't support
            # vector similarity ordering directly
            result = query_builder.execute()
            
            if not result.data:
                log.warning("No results from Supabase query")
                return [], []
            
            # Calculate cosine similarity in Python for now
            # (ideally this would be done in the database, but client limitations)
            import numpy as np
            import json
            
            query_vec = np.array(query_embedding, dtype=np.float32)
            scored_results = []
            
            for row in result.data:
                if row.get('embedding'):
                    # Supabase returns embeddings as lists already (from JSON)
                    embed_data = row['embedding']
                    if isinstance(embed_data, str):
                        # If it's a string, parse it
                        embed_data = json.loads(embed_data)
                    
                    doc_vec = np.array(embed_data, dtype=np.float32)
                    
                    # Cosine similarity
                    dot_product = np.dot(query_vec, doc_vec)
                    norm_product = np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                    if norm_product > 0:
                        similarity = dot_product / norm_product
                        scored_results.append((similarity, row))
            
            # Sort by similarity (highest first)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Take top n_results
            top_results = scored_results[:n_results]
            
            # Convert to ChromaDB-compatible format
            metadatas = []
            documents = []
            
            for similarity, row in top_results:
                metadata = {
                    'name': row['name'],
                    'url': row['url'],
                    'description': row.get('description', ''),
                    'duration': row.get('duration', 0),
                    'adaptive_support': row.get('adaptive_support', 'No'),
                    'remote_support': row.get('remote_support', 'No'),
                    'test_type': row.get('test_type', 'General'),
                    'job_level': row.get('job_level', 'General')
                }
                metadatas.append(metadata)
                documents.append(row['full_text'])
            
            log.info(f"Supabase vector search returned {len(metadatas)} results")
            return metadatas, documents
            
        except Exception as e:
            log.error(f"Supabase vector search failed: {e}")
            import traceback
            log.error(traceback.format_exc())
            
            # Fallback to basic query without vector search
            try:
                result = self.db.table(self.table_name).select("*").limit(n_results).execute()
                metadatas = []
                documents = []
                
                for row in result.data:
                    metadata = {
                        'name': row['name'],
                        'url': row['url'],
                        'description': row.get('description', ''),
                        'duration': row.get('duration', 0),
                        'adaptive_support': row.get('adaptive_support', 'No'),
                        'remote_support': row.get('remote_support', 'No'),
                        'test_type': row.get('test_type', 'General'),
                        'job_level': row.get('job_level', 'General')
                    }
                    metadatas.append(metadata)
                    documents.append(row['full_text'])
                
                log.warning(f"Using fallback: returned {len(metadatas)} random results")
                return metadatas, documents
            except Exception as fallback_error:
                log.error(f"Fallback query also failed: {fallback_error}")
                return [], []
    
    def get_all(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Get all documents from Supabase"""
        try:
            result = self.db.table(self.table_name).select("*").execute()
            
            metadatas = []
            documents = []
            
            for row in result.data:
                metadata = {
                    'name': row['name'],
                    'url': row['url'],
                    'description': row.get('description', ''),
                    'duration': row.get('duration', 0),
                    'adaptive_support': row.get('adaptive_support', 'No'),
                    'remote_support': row.get('remote_support', 'No'),
                    'test_type': row.get('test_type', 'General'),
                    'job_level': row.get('job_level', 'General')
                }
                metadatas.append(metadata)
                documents.append(row['full_text'])
            
            return metadatas, documents
            
        except Exception as e:
            log.error(f"Failed to get all documents from Supabase: {e}")
            return [], []
    
    def count(self) -> int:
        """Get count from Supabase"""
        try:
            result = self.db.table(self.table_name).select("id", count="exact").execute()
            return result.count if hasattr(result, 'count') else 0
        except Exception as e:
            log.error(f"Failed to count documents in Supabase: {e}")
            return 0


def get_vector_db() -> VectorDB:
    """
    Factory function to get the appropriate vector database backend
    
    Returns:
        VectorDB instance (ChromaDB or Supabase)
    """
    db_type = os.getenv("VECTOR_DB_TYPE", "chromadb").lower()
    
    if db_type == "supabase":
        log.info("Using Supabase pgvector backend")
        return SupabaseVectorBackend()
    else:
        log.info("Using ChromaDB backend")
        return ChromaDBBackend()
