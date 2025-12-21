from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any, Union
import uvicorn
import os

app = FastAPI(
    title="Cross-Encoder Reranking API",
    description="Reranking service using cross-encoder/ms-marco-MiniLM-L-6-v2",
    version="1.0.0"
)

# Load model once at startup
MODEL_NAME = os.getenv("MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
try:
    model = CrossEncoder(MODEL_NAME)
    print(f"Loaded CrossEncoder model: {MODEL_NAME}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class RerankRequest(BaseModel):
    query: str
    documents: List[str]  # List of document texts to rerank
    
class RerankResponse(BaseModel):
    scores: List[float]
    ranked_indices: List[int]

@app.get("/")
def root():
    return {
        "message": "Cross-Encoder Reranking API",
        "model": MODEL_NAME,
        "status": "active" if model else "error"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/rerank", response_model=RerankResponse)
def rerank_documents(request: RerankRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        if not request.documents:
            return RerankResponse(scores=[], ranked_indices=[])
            
        # Create pairs [query, doc]
        pairs = [[request.query, doc] for doc in request.documents]
        
        # Predict scores
        scores = model.predict(pairs)
        
        # Convert numpy floats to python floats
        scores_list = scores.tolist() if hasattr(scores, 'tolist') else list(scores)
        
        # Get sorted indices (descending score)
        # Using enumerate to keep track of original index
        indexed_scores = list(enumerate(scores_list))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        ranked_indices = [idx for idx, score in indexed_scores]
        
        return RerankResponse(
            scores=scores_list,
            ranked_indices=ranked_indices
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
