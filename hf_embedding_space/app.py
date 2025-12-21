from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import uvicorn

app = FastAPI(
    title="BGE Embedding API",
    description="Embedding service using BAAI/bge-small-en-v1.5 - optimized for retrieval tasks",
    version="2.0.0"
)

# Load BGE model once at startup - better for semantic search
model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# BGE model instruction prefix for queries
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

class EmbeddingRequest(BaseModel):
    texts: Union[str, List[str]]
    normalize: bool = True
    is_query: bool = False  # Set to True for search queries, False for documents

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str = "BAAI/bge-small-en-v1.5"
    dimension: int = 384

@app.get("/")
def root():
    return {
        "message": "BGE Embedding API - Optimized for Retrieval",
        "model": "BAAI/bge-small-en-v1.5",
        "dimension": 384,
        "features": [
            "Superior semantic search performance",
            "Asymmetric query-document encoding",
            "Instruction-based query prefix support"
        ],
        "endpoints": {
            "embed": "/embed (POST)",
            "health": "/health (GET)"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": True, "model": "BAAI/bge-small-en-v1.5"}

@app.post("/embed", response_model=EmbeddingResponse)
def create_embeddings(request: EmbeddingRequest):
    try:
        # Handle single string or list of strings
        texts = [request.texts] if isinstance(request.texts, str) else request.texts
        
        # Add query prefix if this is a search query (not a document)
        if request.is_query:
            texts = [QUERY_PREFIX + text for text in texts]
        
        # Generate embeddings
        embeddings = model.encode(
            texts,
            normalize_embeddings=request.normalize,
            show_progress_bar=False
        )
        
        # Convert to list format
        embeddings_list = embeddings.tolist()
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimension=len(embeddings_list[0])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)