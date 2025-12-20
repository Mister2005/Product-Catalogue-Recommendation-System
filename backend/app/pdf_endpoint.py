

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
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
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
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file"
            )
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF file: {str(e)}"
        )
    
    # Create a simple request object for the recommender
    from app.models.schemas import RecommendationRequest
    
    simple_request = RecommendationRequest(
        job_title=query_text[:200] if len(query_text) > 200 else query_text,
        required_skills=[],  # Will be extracted by recommender from query
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

