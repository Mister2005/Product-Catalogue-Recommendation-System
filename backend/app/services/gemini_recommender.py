"""
Gemini AI-based recommendation engine
"""
from typing import List, Dict, Optional
import json
import google.generativeai as genai

from app.models.schemas import RecommendationRequest, RecommendationItem, RecommendationScore, AssessmentResponse
from app.core.config import get_settings
from app.core.logging import log

settings = get_settings()


class GeminiRecommender:
    """
    AI-powered recommendation engine using Google Gemini
    """
    
    def __init__(self):
        """Initialize Gemini recommender"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            model_name = settings.gemini_model if hasattr(settings, 'gemini_model') else 'gemini-pro'
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": settings.gemini_temperature if hasattr(settings, 'gemini_temperature') else 0.7,
                    "max_output_tokens": 4096,  # Increased to prevent truncation
                }
            )
            log.info("Gemini recommender initialized")
        else:
            log.warning("Gemini API key not configured")
            self.model = None
    
    def _create_assessment_catalog(self, assessments: List[dict]) -> str:
        """Create formatted assessment catalog"""
        catalog = []
        
        for assessment in assessments:
            entry = {
                "id": assessment.get('id', ''),
                "name": assessment.get('name', ''),
                "type": assessment.get('type', ''),
                "job_family": assessment.get('job_family', ''),
                "job_level": assessment.get('job_level', ''),
                "test_types": [],
                "skills": [][:5],  # Limit for token efficiency
                "industries": [],
                "duration": assessment.get('duration', 0),
                "remote_testing": assessment.get('remote_testing', False),
                "description": (assessment.get('description', '')[:150] + "...") if assessment.get('description', '') and len(assessment.get('description', '')) > 150 else assessment.get('description', '')
            }
            catalog.append(entry)
        
        return json.dumps(catalog, indent=2)
    
    def _create_prompt(self, request: RecommendationRequest, catalog: str) -> str:
        """Create prompt for Gemini"""
        skills_str = ', '.join(request.required_skills[:8]) if request.required_skills else 'Any'
        
        prompt = f"""Select the top {request.num_recommendations} most relevant assessments for:
Job: {request.job_title or 'Any'}
Level: {request.job_level or 'Any'}  
Skills: {skills_str}
Industry: {request.industry or 'Any'}

Assessments:
{catalog}

IMPORTANT: Return ONLY a valid JSON object. Keep explanations brief (max 20 words).
Format: {{"recommendations": [{{"id": "assessment_id", "relevance_score": 0.9, "skill_match_score": 0.85, "explanation": "Brief reason"}}]}}"""
        return prompt
    
    async def recommend(
        self, 
        request: RecommendationRequest, 
        db
    ) -> List[RecommendationItem]:
        """
        Generate recommendations using Gemini AI
        """
        log.info(f"Gemini recommendation for: {request.dict()}")
        
        if not self.model:
            log.warning("Gemini model not initialized - skipping")
            return []
        
        # Get all assessments
        try:
            response = db.table("assessments").select("*").execute()
            assessments = response.data
        except Exception as e:
            log.error(f"Failed to fetch assessments: {e}")
            return []
        
        if not assessments:
            log.warning("No assessments found")
            return []
        
        # Create catalog (limit to reasonable size for token limits)
        # Use 25 assessments to avoid token limit issues
        catalog = self._create_assessment_catalog(assessments[:25])
        
        # Create prompt
        prompt = self._create_prompt(request, catalog)
        log.debug(f"Prompt length: {len(prompt)} chars")
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Log response structure for debugging
            log.debug(f"Gemini response type: {type(response)}")
            
            # Check if response was blocked
            if not response.candidates:
                log.error("Gemini response was blocked (safety filters or empty)")
                if hasattr(response, 'prompt_feedback'):
                    feedback = response.prompt_feedback
                    log.error(f"Prompt feedback: block_reason={getattr(feedback, 'block_reason', 'unknown')}, safety_ratings={getattr(feedback, 'safety_ratings', [])}")
                else:
                    log.debug(f"No prompt feedback available")
                return []
            
            # Log candidate info for debugging
            for i, candidate in enumerate(response.candidates):
                log.debug(f"Candidate {i}: finish_reason={getattr(candidate, 'finish_reason', 'N/A')}")
                if hasattr(candidate, 'content') and candidate.content:
                    log.debug(f"Candidate {i} has content with {len(candidate.content.parts) if hasattr(candidate.content, 'parts') else 0} parts")
            
            # Extract text from response (handle multi-part responses including "thinking" models)
            response_text = ""
            
            # First try the direct .text accessor
            try:
                response_text = response.text
                log.debug(f"Got response using .text accessor, length: {len(response_text)}")
            except ValueError as ve:
                # This happens with models that have "thinking" parts (like gemini-2.5-pro)
                log.debug(f"ValueError with .text accessor: {ve}")
                # Extract text parts manually, skipping "thinking" parts
                try:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                # Check if this is a text part (not a thinking/tool part)
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                    log.debug(f"Extracted text part: {part.text[:100] if len(part.text) > 100 else part.text}...")
                except Exception as ex:
                    log.error(f"Failed to extract text from parts: {ex}")
            except Exception as e:
                # For other exceptions, try the parts accessor
                log.debug(f"Exception with .text accessor: {type(e).__name__}: {e}")
                try:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                    log.debug(f"Extracted text from part: {part.text[:100] if len(part.text) > 100 else part.text}...")
                except Exception as ex:
                    log.error(f"Failed to extract text from parts: {ex}")
                    log.error(f"Response object: {response}")
                    log.error(f"Candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
            
            if not response_text or len(response_text.strip()) == 0:
                log.error("Empty response from Gemini after text extraction")
                log.debug(f"Response candidates: {response.candidates if hasattr(response, 'candidates') else 'No candidates'}")
                # Log the full response structure for debugging
                try:
                    for i, candidate in enumerate(response.candidates):
                        log.error(f"Candidate {i} structure: {dir(candidate)}")
                        if hasattr(candidate, 'content') and candidate.content:
                            log.error(f"Content parts: {len(candidate.content.parts) if hasattr(candidate.content, 'parts') else 0}")
                            for j, part in enumerate(candidate.content.parts):
                                log.error(f"Part {j} type: {type(part)}, attributes: {dir(part)}")
                except Exception as debug_ex:
                    log.error(f"Debug logging failed: {debug_ex}")
                if hasattr(response, 'prompt_feedback'):
                    log.error(f"Prompt feedback: {response.prompt_feedback}")
                # Response is empty or blocked, return empty list
                return []
            
            log.debug(f"Gemini raw response (first 200 chars): {response_text[:200]}")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            response_text = response_text.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse Gemini JSON response: {e}")
                log.error(f"Response text: {response_text[:500]}")
                return []
            
            if not result.get("recommendations"):
                log.warning("No recommendations in Gemini response")
                return []
            
            # Create recommendations
            recommendations = []
            assessment_map = {a.get('id'): a for a in assessments}
            
            for idx, rec in enumerate(result.get("recommendations", [])):
                assessment_id = rec.get("id")
                
                # Try exact match first
                assessment = assessment_map.get(assessment_id)
                
                # If not found, try fuzzy matching (case-insensitive, handle special chars)
                if not assessment:
                    # Try to find by name match or similar ID
                    normalized_id = assessment_id.lower().replace('_', ' ').replace('-', ' ')
                    for db_assessment in assessments:
                        db_id = db_assessment.get('id', '').lower()
                        db_name = db_assessment.get('name', '').lower()
                        
                        # Check if IDs are similar or if name matches
                        if (normalized_id in db_id or db_id in normalized_id or 
                            normalized_id in db_name or db_name in normalized_id):
                            assessment = db_assessment
                            log.info(f"Fuzzy matched '{assessment_id}' to '{db_assessment.get('id')}'")
                            break
                
                if not assessment:
                    log.warning(f"Assessment {assessment_id} not found (skipping)")
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
                
                assessment_response = self._db_to_response(assessment)
                
                score = RecommendationScore(
                    total_score=rec.get("relevance_score", 0.8),
                    relevance_score=rec.get("relevance_score", 0.8),
                    skill_match_score=rec.get("skill_match_score"),
                    confidence=rec.get("relevance_score", 0.8),
                    explanation=rec.get("explanation", "AI-recommended")
                )
                
                recommendations.append(RecommendationItem(
                    assessment=assessment_response,
                    score=score,
                    rank=idx + 1
                ))
            
            log.info(f"Gemini returned {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            log.error(f"Gemini recommendation error: {e}")
            return []
    
    def _db_to_response(self, assessment: dict) -> AssessmentResponse:
        """Convert database model to response schema"""
        return AssessmentResponse(
            id=assessment.get('id', ''),
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


