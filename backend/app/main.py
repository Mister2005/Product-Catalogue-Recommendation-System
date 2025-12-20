"""
Production-ready FastAPI application
Optimized for Render deployment - loads models at startup
"""
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Only import lightweight modules at startup
from app.core.config import get_settings
from app.core.logging import log
from app.models import schemas

settings = get_settings()

# Track initialization state
_initialization_complete = False
_initialization_error = None



def _load_models_sync(app: FastAPI):
    """Synchronous function to load heavy ML models - runs in thread pool"""
    import gc
    log.info("Loading ML models in background thread (Sequential Mode)...")
    
    models = {}
    
    try:
        # 1. NLP Recommender (Lightweight)
        log.info("Loading NLP Recommender...")
        from app.services.nlp_recommender import NLPRecommender
        models["nlp"] = NLPRecommender()
        gc.collect()
        
        # 2. Clustering Recommender (Medium)
        log.info("Loading Clustering Recommender...")
        from app.services.clustering_recommender import ClusteringRecommender
        models["clustering"] = ClusteringRecommender()
        gc.collect()
        
        # 3. Gemini Recommender (Lightweight API)
        log.info("Loading Gemini Recommender...")
        from app.services.gemini_recommender import GeminiRecommender
        models["gemini"] = GeminiRecommender()
        gc.collect()
        
        # 4. RAG Recommender (Heavy - Load Last)
        log.info("Loading RAG Recommender...")
        from app.services.rag_recommender import RAGRecommender
        models["rag"] = RAGRecommender()
        gc.collect()
        
        # 5. Hybrid Recommender (Wrapper)
        log.info("Initializing Hybrid Recommender...")
        from app.services.hybrid_recommender import HybridRecommender
        models["hybrid"] = HybridRecommender(
            rag_recommender=models["rag"],
            nlp_recommender=models["nlp"],
            clustering_recommender=models["clustering"],
            gemini_recommender=models["gemini"]
        )
        gc.collect()
        
        log.info("All models loaded successfully")
        return models
        
    except Exception as e:
        log.error(f"Critical error loading models: {e}")
        # Return whatever we have, or raise
        raise e



# Validating if models are loaded
async def ensure_models_loaded(app: FastAPI):
    """Ensure ML models are loaded (fallback for startup failure)"""
    if hasattr(app.state, "rag_recommender") and app.state.rag_recommender:
        return

    log.warning("Models not loaded at startup. Loading now (this may take 2-3 minutes)...")
    loop = asyncio.get_running_loop()
    
    # Run blocking model loading in executor
    models = await loop.run_in_executor(None, _load_models_sync, app)
    
    # Assign initialized models to app state
    app.state.rag_recommender = models["rag"]
    app.state.nlp_recommender = models["nlp"]
    app.state.clustering_recommender = models["clustering"]
    app.state.gemini_recommender = models["gemini"]
    app.state.hybrid_recommender = models["hybrid"]
    
    log.info("Models loaded successfully")


async def initialize_connections(app: FastAPI):
    """Initialize lightweight connections (DB, Redis)"""
    log.info("Initializing database and cache connections...")
    
    try:
        # Import lightweight modules
        from app.core.database import get_supabase_client
        from app.core.cache import cache
        
        # Connect to cache
        try:
            await cache.connect()
            log.info("Connected to Redis cache")
        except Exception as e:
            log.warning(f"Redis connection failed (continuing without cache): {e}")
        
        # Test Supabase connection
        try:
            supabase = get_supabase_client()
            log.info(f"Connected to Supabase: {settings.supabase_url}")
        except Exception as e:
            log.error(f"Supabase connection failed: {str(e)}")
            
    except Exception as e:
        log.error(f"Error initializing connections: {e}")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - load models at startup"""
    # Startup
    log.info("Starting SHL Recommendation Engine...")
    
    # Initialize basic connections (DB, Redis)
    await initialize_connections(app)
    
    # Load ML models at startup (in background thread to not block)
    log.info("Loading ML models at startup...")
    loop = asyncio.get_running_loop()
    
    try:
        # Run blocking model loading in executor
        models = await loop.run_in_executor(None, _load_models_sync, app)
        
        # Assign initialized models to app state
        app.state.rag_recommender = models["rag"]
        app.state.nlp_recommender = models["nlp"]
        app.state.clustering_recommender = models["clustering"]
        app.state.gemini_recommender = models["gemini"]
        app.state.hybrid_recommender = models["hybrid"]
        
        log.info("✅ All models loaded and ready!")
    except Exception as e:
        log.error(f"Failed to load models at startup: {e}")
        # Set error state but continue - models can be loaded on-demand
        global _initialization_error
        _initialization_error = str(e)
    
    # Ready to serve
    global _initialization_complete
    _initialization_complete = True
    
    log.info("🚀 Server ready - All models loaded!")
    
    yield

    
    # Shutdown
    log.info("Shutting down SHL Recommendation Engine")
    try:
        from app.core.cache import cache
        await cache.disconnect()
    except:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="Production-ready recommendation engine for SHL assessments with multiple AI/ML approaches",
    version=settings.version,
    lifespan=lifespan
)

# CORS middleware
# CORS middleware - Modified to allow Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SHL Assessment Recommendation Engine v2.0</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 50px auto; padding: 30px; background: #f5f7fa; }
            .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-bottom: 10px; }
            .version { color: #7f8c8d; font-size: 14px; margin-bottom: 30px; }
            .feature { background: #ecf0f1; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #3498db; }
            .feature h3 { margin-top: 0; color: #2980b9; }
            .endpoint { background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .endpoint code { background: #c8e6c9; padding: 3px 8px; border-radius: 3px; }
            .button { display: inline-block; background: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            .button:hover { background: #2980b9; }
            .engines { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px; }
            .engine-card { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 SHL Assessment Recommendation Engine</h1>
            <p class="version">Version 2.0 - Production Ready</p>
            
            <div class="feature">
                <h3>🚀 New Features</h3>
                <ul>
                    <li><strong>PostgreSQL Database</strong> - Migrated from JSON to production SQL database</li>
                    <li><strong>RAG System</strong> - Semantic search using sentence transformers</li>
                    <li><strong>Multiple Engines</strong> - Gemini AI, NLP, Clustering, and Hybrid approaches</li>
                    <li><strong>Redis Caching</strong> - High-performance result caching</li>
                    <li><strong>Production Architecture</strong> - Clean, scalable, and maintainable</li>
                </ul>
            </div>
            
            <div class="engines">
                <div class="engine-card">
                    <strong>🤖 Gemini AI</strong><br>
                    <small>AI-powered intelligent recommendations</small>
                </div>
                <div class="engine-card">
                    <strong>🔍 RAG</strong><br>
                    <small>Semantic vector search</small>
                </div>
                <div class="engine-card">
                    <strong>📊 NLP</strong><br>
                    <small>TF-IDF based matching</small>
                </div>
                <div class="engine-card">
                    <strong>🎲 Clustering</strong><br>
                    <small>K-Means + UMAP</small>
                </div>
            </div>
            
            <h2>📚 API Endpoints:</h2>
            
            <div class="endpoint">
                <strong>POST</strong> <code>/api/v1/recommend</code><br>
                <small>Get personalized recommendations with engine selection</small>
            </div>
            
            <div class="endpoint">
                <strong>GET</strong> <code>/api/v1/assessments</code><br>
                <small>List all available assessments</small>
            </div>
            
            <div class="endpoint">
                <strong>GET</strong> <code>/api/v1/assessments/{id}</code><br>
                <small>Get specific assessment details</small>
            </div>
            
            <div class="endpoint">
                <strong>GET</strong> <code>/api/v1/metadata</code><br>
                <small>Get system metadata (job families, industries, skills)</small>
            </div>
            
            <div class="endpoint">
                <strong>POST</strong> <code>/api/v1/feedback</code><br>
                <small>Submit feedback on recommendations</small>
            </div>
            
            <div class="endpoint">
                <strong>GET</strong> <code>/health</code><br>
                <small>System health check</small>
            </div>
            
            <a href="/docs" class="button">📖 Interactive API Documentation</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check endpoint - returns quickly for port detection"""
    global _initialization_complete, _initialization_error
    
    # Always return quickly to satisfy Render's port detection
    if not _initialization_complete:
        return {
            "status": "starting",
            "version": settings.version,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Services initializing...",
            "error": _initialization_error
        }
    
    # Full health check once initialized
    try:
        from app.core.database import get_supabase_client
        from app.core.cache import cache
        
        db = get_supabase_client()
        db.table("assessments").select("id").limit(1).execute()
        db_status = "healthy"
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check cache
    try:
        await cache.set("health_check", "ok", ttl=10)
        cache_status = "healthy"
    except:
        cache_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": settings.version,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "cache": cache_status
    }


# NEW SIMPLIFIED ENDPOINT (SHL Assignment)
@app.post("/recommend", response_model=schemas.RecommendResponse)
async def recommend(
    request: schemas.RecommendRequest,
    http_request: Request
):
    """
    Simplified recommendation endpoint for SHL Assignment
    
    Accepts:
        - query: Natural language query or job description text
        - url: URL containing job description
    
    Returns:
        - List of assessment recommendations (name + URL only)
        - Min 1, max 10 recommendations
        - Only Individual Test Solutions
    """
    # Ensure models are loaded
    await ensure_models_loaded(http_request.app)
    
    from app.core.database import get_supabase_client
    from app.utils.url_extractor import extract_text_from_url, is_valid_url
    from pypdf import PdfReader
    from io import BytesIO
    
    db = get_supabase_client()
    
    # Determine query text from multiple sources
    query_text = None
    
    if url:
        # Fetch and extract text from URL
        if not is_valid_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL provided")
        
        try:
            query_text = await extract_text_from_url(request.url)
            log.info(f"Extracted {len(query_text)} characters from URL: {request.url}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif request.query:
        query_text = request.query
    else:
        raise HTTPException(status_code=400, detail="Either query or url must be provided")
    
    # Create a simple request object for the recommender
    # Use hybrid recommender by default for best results
    from app.models.schemas import RecommendationRequest
    
    simple_request = RecommendationRequest(
        job_title=query_text[:200] if len(query_text) > 200 else query_text,  # Use query as job title
        required_skills=[],  # Will be extracted by recommender from query
        num_recommendations=10,  # Always get 10 (max allowed)
        engine="hybrid"
    )
    
    # Get recommendations using hybrid recommender
    recommender = http_request.app.state.hybrid_recommender
    recommendations = await recommender.recommend(simple_request, db)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No suitable assessments found")
    
    # Filter to only Individual Test Solutions and limit to 10
    individual_test_recommendations = [
        r for r in recommendations 
        if r.assessment.type == "Individual Test Solution"
    ][:10]
    
    if not individual_test_recommendations:
        raise HTTPException(
            status_code=404, 
            detail="No Individual Test Solutions found for your query"
        )
    
    # Convert to simplified response format
    simplified_recommendations = []
    
    # Import URL mapper
    from app.utils.url_mapper import get_url_mapper
    url_mapper = get_url_mapper()
    
    for rec in individual_test_recommendations:
        assessment = rec.assessment
        
        # Get URL from mapper using assessment name
        assessment_url = url_mapper.get_url_from_name(assessment.name)
        
        simplified_recommendations.append(
            schemas.AssessmentRecommendation(
                assessment_name=assessment.name,
                assessment_url=assessment_url
            )
        )
    
    # Ensure we have at least 1 recommendation
    if len(simplified_recommendations) < 1:
        raise HTTPException(
            status_code=404,
            detail="No suitable Individual Test Solutions found"
        )
    
    return schemas.RecommendResponse(
        recommendations=simplified_recommendations
    )


# PDF UPLOAD ENDPOINT
@app.post("/recommend/pdf", response_model=schemas.RecommendResponse)
async def recommend_from_pdf(
    file: UploadFile = File(...),
    http_request: Request = None
):
    """
    PDF Upload endpoint for job description recommendations
    
    Accepts:
        - file: PDF file containing job description
    
    Returns:
        - List of assessment recommendations (name + URL only)
        - Min 1, max 10 recommendations
        - Only Individual Test Solutions
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Ensure models are loaded
    await ensure_models_loaded(http_request.app)
    
    from app.core.database import get_supabase_client
    from app.utils.pdf_extractor import extract_text_from_pdf, validate_pdf
    
    db = get_supabase_client()
    
    # Read PDF content
    try:
        pdf_content = await file.read()
        
        # Validate PDF
        if not validate_pdf(pdf_content):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        
        # Extract text from PDF
        query_text = extract_text_from_pdf(pdf_content)
        
        if not query_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. Please ensure the PDF contains readable text."
            )
        
        log.info(f"Extracted {len(query_text)} characters from PDF: {file.filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF file: {str(e)}")
    
    # Create a simple request object for the recommender
    from app.models.schemas import RecommendationRequest
    
    simple_request = RecommendationRequest(
        job_title=query_text[:200] if len(query_text) > 200 else query_text,
        required_skills=[],
        num_recommendations=10,
        engine="hybrid"
    )
    
    # Get recommendations using hybrid recommender
    recommender = http_request.app.state.hybrid_recommender
    recommendations = await recommender.recommend(simple_request, db)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No suitable assessments found")
    
    # Filter to only Individual Test Solutions and limit to 10
    individual_test_recommendations = [
        r for r in recommendations 
        if r.assessment.type == "Individual Test Solution"
    ][:10]
    
    if not individual_test_recommendations:
        raise HTTPException(
            status_code=404, 
            detail="No Individual Test Solutions found for your query"
        )
    
    # Convert to simplified response format
    simplified_recommendations = []
    
    # Import URL mapper
    from app.utils.url_mapper import get_url_mapper
    url_mapper = get_url_mapper()
    
    for rec in individual_test_recommendations:
        assessment = rec.assessment
        assessment_url = url_mapper.get_url_from_name(assessment.name)
        
        simplified_recommendations.append(
            schemas.AssessmentRecommendation(
                assessment_name=assessment.name,
                assessment_url=assessment_url
            )
        )
    
    if len(simplified_recommendations) < 1:
        raise HTTPException(
            status_code=404,
            detail="No suitable Individual Test Solutions found"
        )
    
    return schemas.RecommendResponse(
        recommendations=simplified_recommendations
    )


# OLD COMPLEX ENDPOINT (Deprecated - keeping for backward compatibility)
@app.post(f"{settings.api_v1_prefix}/recommend", response_model=schemas.RecommendationResponse)
async def get_recommendations(
    http_request: Request,
):
    """
    Get personalized assessment recommendations
    
    Supports multiple recommendation engines:
    - gemini: AI-powered recommendations using Google Gemini
    - rag: Semantic search using RAG
    - nlp: Traditional NLP with TF-IDF
    - clustering: K-Means clustering based
    - hybrid: Combined approach (default)
    
    Can accept either JSON body or multipart/form-data for file uploads.
    """
    # On-Demand Loading: Ensure models are loaded before processing
    await ensure_models_loaded(http_request.app)
    
    # Import modules after ensuring models are loaded (though they are loaded into app.state)
    import json
    from app.core.database import get_supabase_client
    from app.core.cache import cache
    from app.services.resume_parser import ResumeParser
    from app.services.github_analyzer import GitHubAnalyzer
    
    db = get_supabase_client()
    
    # Determine content type
    content_type = http_request.headers.get("content-type", "")
    request = None
    
    # Handle multipart/form-data (file upload)
    if "multipart/form-data" in content_type:
        form = await http_request.form()
        resume_file = form.get("resume_file")
        github_url = form.get("github_url")
        
        # Extract form fields
        job_title = form.get("job_title")
        job_family = form.get("job_family")
        job_level = form.get("job_level")
        industry = form.get("industry")
        required_skills_str = form.get("required_skills")
        test_types_str = form.get("test_types")
        remote_testing_required = form.get("remote_testing_required") == "true"
        max_duration = int(form.get("max_duration")) if form.get("max_duration") else None
        language = form.get("language")
        num_recommendations = int(form.get("num_recommendations", 10))
        engine = form.get("engine", "hybrid")
        user_id = form.get("user_id")
        
        log.info(f"📄 File upload mode - Resume: {resume_file.filename if resume_file else None}, GitHub: {github_url}")
        
        # Initialize parsers
        resume_parser = ResumeParser()
        github_analyzer = GitHubAnalyzer(github_token=settings.github_token if hasattr(settings, 'github_token') else None)
        
        # Parse resume if provided
        resume_data = {}
        if resume_file:
            resume_content = await resume_file.read()
            resume_data = await resume_parser.parse_resume(resume_content, resume_file.filename)
            log.info(f"📋 Resume parsed: {len(resume_data.get('skills', []))} skills extracted")
        
        # Analyze GitHub if URL provided
        github_data = {}
        if github_url:
            github_data = await github_analyzer.analyze_profile(github_url)
            log.info(f"🐙 GitHub analyzed: {len(github_data.get('skills', []))} skills, {len(github_data.get('languages', []))} languages")
        
        # Combine skills from resume, GitHub, and form
        all_skills = set(resume_data.get('skills', []))
        if github_data:
            all_skills.update(github_data.get('skills', []))
            all_skills.update(github_data.get('languages', []))
        if required_skills_str:
            all_skills.update(json.loads(required_skills_str))
        
        # Use extracted or form data (form takes priority if provided)
        extracted_job_title = job_title or resume_data.get('job_title')
        extracted_job_level = job_level or resume_data.get('job_level') or github_data.get('job_level', 'Entry Level')
        extracted_industry = industry or resume_data.get('industry') or 'Technology'
        
        # Build request with extracted information
        request = schemas.RecommendationRequest(
            job_title=extracted_job_title,
            job_family=job_family,
            job_level=extracted_job_level,
            industry=extracted_industry,
            required_skills=sorted(list(all_skills)),
            test_types=json.loads(test_types_str) if test_types_str else [],
            remote_testing_required=remote_testing_required,
            max_duration=max_duration,
            language=language,
            num_recommendations=num_recommendations,
            engine=engine,
            user_id=user_id
        )
        
        log.info(f"✅ Smart extraction complete: Job: {extracted_job_title}, Level: {extracted_job_level}, Skills: {len(request.required_skills)}")
        log.info(f"📊 Extracted skills: {', '.join(request.required_skills[:10])}{'...' if len(request.required_skills) > 10 else ''}")
    else:
        # Handle JSON body
        try:
            body = await http_request.json()
            request = schemas.RecommendationRequest(**body)
            log.info(f"📝 JSON mode - Request received with {len(request.required_skills)} skills")
        except Exception as e:
            log.error(f"Failed to parse JSON body: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    if not request:
        raise HTTPException(status_code=400, detail="No request data provided")
    
    log.info(f"Recommendation request: {request.dict()}")
    
    # Check cache
    cache_key = f"recommend:{hash(str(request.dict()))}"
    cached = await cache.get(cache_key)
    
    if cached:
        log.info("Returning cached recommendations")
        return cached
    
    # Select recommender
    if request.engine == schemas.RecommendationEngineEnum.GEMINI:
        recommender = app.state.gemini_recommender
    elif request.engine == schemas.RecommendationEngineEnum.RAG:
        recommender = app.state.rag_recommender
    elif request.engine == schemas.RecommendationEngineEnum.NLP:
        recommender = app.state.nlp_recommender
    elif request.engine == schemas.RecommendationEngineEnum.CLUSTERING:
        recommender = app.state.clustering_recommender
    else:  # hybrid
        recommender = app.state.hybrid_recommender
    
    # Get recommendations
    recommendations = await recommender.recommend(request, db)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No suitable assessments found")
    
    # Create response
    response = schemas.RecommendationResponse(
        recommendations=recommendations,
        total_count=len(recommendations),
        engine_used=request.engine if isinstance(request.engine, str) else request.engine.value,
        query_summary=f"Job: {request.job_title or 'Any'}, Level: {request.job_level or 'Any'}, Industry: {request.industry or 'Any'}",
        metadata={"request": request.dict()}
    )
    
    # Save to history
    try:
        history_data = {
            "user_id": request.user_id,
            "query_text": response.query_summary,
            "query_parameters": request.dict(),
            "recommended_assessments": [r.assessment.dict() for r in recommendations],
            "recommendation_engine": request.engine if isinstance(request.engine, str) else request.engine.value,
            "scores": [r.score.dict() for r in recommendations]
        }
        result = db.table("recommendation_history").insert(history_data).execute()
        if result.data:
            from uuid import UUID
            rec_id = result.data[0].get("id")
            response.recommendation_id = UUID(rec_id) if isinstance(rec_id, str) else rec_id
    except Exception as e:
        log.error(f"Failed to save recommendation history: {e}")
    
    # Cache result
    await cache.set(cache_key, response.dict(), ttl=3600)
    
    return response


@app.get(f"{settings.api_v1_prefix}/assessments", response_model=List[schemas.AssessmentResponse])
async def list_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    job_family: str = Query(None),
):
    """List all assessments with pagination and filtering"""
    from app.core.database import get_supabase_client
    db = get_supabase_client()
    
    # Use assessment_details view which includes array fields
    query = db.from_("assessment_details").select("*")
    
    if job_family:
        query = query.ilike("job_family", f"%{job_family}%")
    
    response = query.range(skip, skip + limit - 1).execute()
    
    return response.data


@app.get(f"{settings.api_v1_prefix}/assessments/{{assessment_id}}")
async def get_assessment(assessment_id: str):
    """Get specific assessment by ID"""
    from app.core.database import get_supabase_client
    db = get_supabase_client()
    
    # Use assessment_details view which includes array fields
    response = db.from_("assessment_details").select("*").eq("id", assessment_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return response.data[0]


@app.get(f"{settings.api_v1_prefix}/metadata")
async def get_metadata():
    """Get system metadata"""
    from app.core.database import get_supabase_client
    from app.core.cache import cache
    
    # Check cache
    cached = await cache.get("metadata")
    if cached:
        return cached
    
    db = get_supabase_client()
    
    # Get all assessments
    response = db.table("assessments").select("*").execute()
    assessments = response.data
    
    job_families = set()
    industries = set()
    job_levels = set()
    languages = {"English", "Spanish", "French", "German", "Portuguese", "Chinese", "Japanese"}  # Default languages
    
    # Extract unique values from assessments
    for assessment in assessments:
        if assessment.get('job_family'):
            job_families.add(assessment['job_family'])
        if assessment.get('job_level'):
            job_levels.add(assessment['job_level'])
    
    # Since we simplified the schema, use common values
    metadata = schemas.MetadataResponse(
        job_families=sorted(list(job_families)) if job_families else ["Sales", "Technology", "Healthcare", "Finance"],
        industries=["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Education"],
        skills=["Communication", "Leadership", "Problem Solving", "Teamwork", "Analytical"],
        test_types=["C", "P", "A", "B", "K", "S", "E", "D"],
        job_levels=sorted(list(job_levels)) if job_levels else ["Entry Level", "Intermediate", "Senior", "Executive"],
        languages=sorted(list(languages))
    )
    
    # Cache for 1 hour
    await cache.set("metadata", metadata.dict(), ttl=3600)
    
    return metadata


@app.post(f"{settings.api_v1_prefix}/feedback")
async def submit_feedback(
    feedback: schemas.FeedbackCreate,
):
    """Submit user feedback on recommendation"""
    from app.core.database import get_supabase_client
    db = get_supabase_client()
    
    try:
        # Insert feedback into Supabase
        data = {
            "recommendation_id": str(feedback.recommendation_id),
            "assessment_id": feedback.assessment_id,
            "rating": feedback.rating,
            "feedback_text": feedback.feedback_text,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.table("user_feedback").insert(data).execute()
        
        return {"status": "success", "message": "Feedback submitted"}
    except Exception as e:
        log.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@app.post(f"{settings.api_v1_prefix}/export-pdf")
async def export_recommendations_pdf(
    data: schemas.RecommendationResponse,
):
    """
    Export recommendations as PDF
    
    Args:
        data: Recommendation response data to export
        
    Returns:
        PDF file as downloadable response
    """
    from fastapi.responses import StreamingResponse
    from app.utils.pdf_generator import PDFGenerator
    
    try:
        log.info(f"Generating PDF for {len(data.recommendations)} recommendations")
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        pdf_buffer = pdf_generator.generate_pdf(data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SHL_Recommendations_{timestamp}.pdf"
        
        # Return as downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        log.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@app.post(f"{settings.api_v1_prefix}/chat")
async def chat(
    chat_request: schemas.ChatRequest,
):
    """Chat with AI assistant for queries and recommendations"""
    from app.core.database import get_supabase_client
    db = get_supabase_client()
    
    try:
        # Build context from database if needed
        context = ""
        
        # Check if user is asking for recommendations
        message_lower = chat_request.message.lower()
        if any(word in message_lower for word in ['recommend', 'suggest', 'find', 'assessment', 'test']):
            # Get some sample assessments for context
            response = db.table("assessments").select("*").limit(5).execute()
            assessments = response.data
            context = "\n\nAvailable assessments:\n"
            for assessment in assessments:
                context += f"- {assessment.get('name', 'Unknown')}: {assessment.get('description', 'No description')}\n"
        
        # Build conversation history
        history_text = ""
        for msg in chat_request.history:
            history_text += f"{msg.role.upper()}: {msg.content}\n"
        
        # Create prompt for Gemini
        prompt = f"""You are an AI assistant for SHL Assessment Recommendation Engine. 
Help users find the right assessments, answer questions about assessments, and provide guidance.

Conversation History:
{history_text}

User Question: {chat_request.message}
{context}

Provide a helpful, concise, and friendly response. If the user asks for recommendations, explain what assessments might be suitable and why."""
        
        # Get response from Gemini
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        # Use gemini-pro which is available in v1beta API
        model_name = settings.gemini_model if hasattr(settings, 'gemini_model') else 'gemini-pro'
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(prompt)
        
        return {
            "response": response.text,
            "context": context if context else None
        }
        
    except Exception as e:
        log.error(f"Chat error: {str(e)}")
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support.",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000, reload=settings.debug)
