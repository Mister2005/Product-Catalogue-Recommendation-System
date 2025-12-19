from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List, Union
import uvicorn
app = FastAPI(
    title="MiniLM Embedding API",
    description="Embedding service using sentence-transformers/all-MiniLM-L6-v2",
    version="1.0.0"
)
# Load model once at startup
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
class EmbeddingRequest(BaseModel):
    texts: Union[str, List[str]]
    normalize: bool = True
class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
@app.get("/")
def root():
    return {
        "message": "MiniLM Embedding API",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
        "endpoints": {
            "embed": "/embed (POST)",
            "health": "/health (GET)"
        }
    }
@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": True}
@app.post("/embed", response_model=EmbeddingResponse)
def create_embeddings(request: EmbeddingRequest):
    try:
        # Handle single string or list of strings
        texts = [request.texts] if isinstance(request.texts, str) else request.texts
        
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