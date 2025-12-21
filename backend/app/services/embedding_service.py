"""
HuggingFace Embedding Service
Provides embeddings using HuggingFace Inference API instead of local models
This reduces memory usage significantly for deployment on Render
"""
import os
import time
from typing import List, Union
from huggingface_hub import InferenceClient
import numpy as np

from app.core.config import get_settings
from app.core.logging import log

settings = get_settings()


class HuggingFaceEmbeddingService:
    """
    Embedding service using HuggingFace Inference API
    Replaces local sentence-transformers to reduce memory footprint
    """
    
    def __init__(self):
        """Initialize HuggingFace client"""
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.model_name = settings.embedding_model
        self.dimension = settings.vector_dimension
        self.use_space = os.getenv('USE_HUGGINGFACE_SPACE', 'false').lower() == 'true'
        self.space_url = os.getenv('HUGGINGFACE_SPACE_URL')
        
        if not self.api_key:
            # Try loading .env explicitly
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Try finding .env in current or parent directory
            current_dir = Path.cwd()
            env_path = current_dir / ".env"
            if not env_path.exists():
                env_path = current_dir / "backend" / ".env"
            
            if env_path.exists():
                log.info(f"Loading environment from {env_path}")
                load_dotenv(env_path)
                self.api_key = os.getenv('HUGGINGFACE_API_KEY')
                self.use_space = os.getenv('USE_HUGGINGFACE_SPACE', 'false').lower() == 'true'
                self.space_url = os.getenv('HUGGINGFACE_SPACE_URL')
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is required")
        
        # Initialize client
        self.client = InferenceClient(token=self.api_key)
        
        log.info(f"HuggingFace embedding service initialized")
        log.info(f"Model: {self.model_name}")
        log.info(f"Using custom Space: {self.use_space}")
        if self.use_space and self.space_url:
            log.info(f"Space URL: {self.space_url}")
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
        batch_size: int = 32,
        max_retries: int = 3,
        is_query: bool = False  # New parameter for query vs document encoding
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts to embed
            normalize_embeddings: Whether to normalize embeddings
            show_progress_bar: Ignored (for compatibility with sentence-transformers)
            batch_size: Number of texts to process in one batch
            max_retries: Maximum number of retry attempts
            is_query: Whether this is a query (True) or document (False)
            
        Returns:
            numpy array of embeddings
        """
        # Convert single string to list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # Use custom Space if configured
        if self.use_space and self.space_url:
            return self._encode_via_space(texts, normalize_embeddings, batch_size, max_retries, is_query)
        
        # Otherwise use HuggingFace Inference API
        return self._encode_via_inference_api(texts, normalize_embeddings, batch_size, max_retries, is_query)
    
    def _encode_via_inference_api(
        self, 
        texts: List[str], 
        normalize: bool,
        batch_size: int,
        max_retries: int,
        is_query: bool = False
    ) -> np.ndarray:
        """Encode using HuggingFace Inference API with improved timeout handling"""
        all_embeddings = []
        
        # Process in batches to handle rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    # Call feature extraction API with longer timeout
                    if len(batch) == 1:
                        # Single text
                        embedding = self.client.feature_extraction(
                            text=batch[0],
                            model=self.model_name,
                            timeout=60.0  # Increased timeout to 60 seconds
                        )
                        # Handle different response formats
                        if isinstance(embedding, list) and len(embedding) > 0:
                            if isinstance(embedding[0], list):
                                # Already in correct format
                                batch_embeddings = embedding
                            else:
                                # Single embedding
                                batch_embeddings = [embedding]
                        else:
                            batch_embeddings = [embedding]
                    else:
                        # Multiple texts - process individually due to API limitations
                        batch_embeddings = []
                        for text in batch:
                            emb = self.client.feature_extraction(
                                text=text,
                                model=self.model_name,
                                timeout=60.0  # Increased timeout
                            )
                            # Ensure it's a list
                            if isinstance(emb, list) and len(emb) > 0 and isinstance(emb[0], list):
                                batch_embeddings.append(emb[0])
                            else:
                                batch_embeddings.append(emb)
                    
                    all_embeddings.extend(batch_embeddings)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Handle different error types
                    if "timeout" in error_msg or "504" in error_msg:
                        if attempt < max_retries - 1:
                            # Timeout error - wait longer before retry
                            wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                            log.warning(f"Timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s before retry")
                            time.sleep(wait_time)
                        else:
                            log.error(f"Failed after {max_retries} timeout attempts: {e}")
                            raise
                    elif "rate limit" in error_msg:
                        if attempt < max_retries - 1:
                            # Rate limited, wait and retry
                            wait_time = (attempt + 1) * 3  # 3s, 6s, 9s
                            log.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                            time.sleep(wait_time)
                        else:
                            log.error(f"Rate limit exceeded after {max_retries} attempts")
                            raise
                    else:
                        # Other error - log and raise
                        log.error(f"Error generating embeddings: {e}")
                        raise
        
        # Convert to numpy array
        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        
        # Normalize if requested
        if normalize:
            norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
            embeddings_array = embeddings_array / np.maximum(norms, 1e-12)
        
        return embeddings_array
    
    def _encode_via_space(
        self, 
        texts: List[str], 
        normalize: bool,
        batch_size: int,
        max_retries: int,
        is_query: bool = False
    ) -> np.ndarray:
        """Encode using custom HuggingFace Space"""
        import requests
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"{self.space_url}/embed",
                        json={"texts": batch, "normalize": normalize, "is_query": is_query},
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    batch_embeddings = data.get("embeddings", [])
                    all_embeddings.extend(batch_embeddings)
                    break  # Success
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        log.warning(f"Space request failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        log.error(f"Failed to get embeddings from Space: {e}")
                        raise
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# Global singleton instance
_embedding_service = None


def get_embedding_service() -> HuggingFaceEmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = HuggingFaceEmbeddingService()
    return _embedding_service
