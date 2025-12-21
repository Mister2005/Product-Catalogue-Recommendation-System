from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import io
import pypdf
import requests
from bs4 import BeautifulSoup

from app.models.api import RecommendationRequest, RecommendationResponse, HealthCheck, ChatRequest, ChatResponse
from app.services.enhanced_hybrid_recommender import EnhancedHybridRecommender
from app.services.embedding_service import HuggingFaceEmbeddingService

# Setup Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Global Service
recommender: EnhancedHybridRecommender = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global recommender
    log.info("Starting up... initializing recommender")
    try:
        recommender = EnhancedHybridRecommender()
        # Verify connection?
        log.info("Recommender initialized successfully")
    except Exception as e:
        log.error(f"Failed to initialize recommender: {e}")
        raise e
    yield
    # Shutdown
    log.info("Shutting down...")

app = FastAPI(title="SHL Assessment Recommender", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    if not recommender:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        query_text = request.query
        
        # Priority 1: URL Content
        if request.url:
            log.info(f"Fetching content from URL: {request.url}")
            try:
                # Fetch URL content
                resp = requests.get(request.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Remove non-content elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                    
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                
                # Truncate to reasonable length for embedding (e.g. 4000 chars)
                query_text = text[:4000]
                log.info(f"Extracted {len(query_text)} chars from URL")
                
            except Exception as e:
                log.error(f"Failed to fetch content from URL: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")
        
        # Validation
        if not query_text:
            raise HTTPException(status_code=400, detail="Either 'query' or 'url' must be provided")

        # Get recommendations
        results = recommender.recommend(query_text)
        return results
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommend", response_model=RecommendationResponse)
async def get_recommendations_v1(request: RecommendationRequest):
    """Alias for /recommend to support different frontend paths"""
    return await get_recommendations(request)

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not recommender:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Convert Pydantic models to dicts for the service
        history_dicts = [h.model_dump() for h in request.history]
        response_text = recommender.chat(request.message, history_dicts)
        return {"response": response_text}
    except Exception as e:
        log.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend/pdf", response_model=RecommendationResponse)
async def recommend_pdf(file: UploadFile = File(...)):
    if not recommender:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Read file content
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        # Parse PDF
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # Limit text length to avoid token limits (approx 1000 words or 4000 chars)
        text = text[:4000]
        
        log.info(f"Extracted {len(text)} chars from PDF")
        
        # Use extracted text as query
        results = recommender.recommend(text)
        return results
    except Exception as e:
        log.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
