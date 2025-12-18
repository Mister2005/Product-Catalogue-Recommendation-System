"""
NLP-based recommendation engine using TF-IDF and advanced text matching
"""
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.schemas import RecommendationRequest, RecommendationItem, RecommendationScore, AssessmentResponse
from app.core.logging import log


class NLPRecommender:
    """
    Traditional NLP-based recommender using TF-IDF
    """
    
    def __init__(self):
        """Initialize NLP recommender"""
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 3),
            max_features=1000,
            min_df=1,
            max_df=0.95
        )
        self.tfidf_matrix = None
        self.assessments_cache = []
    
    def _create_assessment_document(self, assessment: dict) -> str:
        """Create document representation"""
        parts = [
            assessment.get('name', ''),
            assessment.get('type', ''),
            assessment.get('job_family', '') or "",
            assessment.get('job_level', '') or "",
            assessment.get('description', '') or ""
        ]
        
        # Add test types
        parts.extend([])
        
        # Add skills with higher weight
        skills = []
        parts.extend(skills * 2)  # Weight skills more
        
        # Add industries
        parts.extend([])
        
        return " ".join(parts)
    
    def fit(self, db):
        """Fit the vectorizer on all assessments"""
        log.info("Fitting NLP recommender")
        
        response = db.table("assessments").select("*").execute()
        assessments = response.data
        self.assessments_cache = assessments
        
        if not assessments:
            log.warning("No assessments found")
            return
        
        # Create documents
        documents = [self._create_assessment_document(a) for a in assessments]
        
        # Fit and transform
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        log.info(f"NLP recommender fitted on {len(assessments)} assessments")
    
    def _create_query_document(self, request: RecommendationRequest) -> str:
        """Create query document"""
        parts = []
        
        if request.job_title:
            parts.append(request.job_title * 2)  # Weight job title
        
        if request.job_family:
            parts.append(request.job_family)
        
        if request.job_level:
            parts.append(request.job_level)
        
        if request.industry:
            parts.append(request.industry)
        
        if request.required_skills:
            parts.extend(request.required_skills * 2)  # Weight skills
        
        if request.test_types:
            parts.extend([tt.value if hasattr(tt, 'value') else tt for tt in request.test_types])
        
        return " ".join(parts) if parts else "general assessment"
    
    async def recommend(
        self, 
        request: RecommendationRequest, 
        db
    ) -> List[RecommendationItem]:
        """
        Generate recommendations using NLP
        """
        log.info(f"NLP recommendation for: {request.dict()}")
        
        if self.tfidf_matrix is None:
            self.fit(db)
        
        # Create query vector
        query_doc = self._create_query_document(request)
        query_vector = self.vectorizer.transform([query_doc])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        # Get top indices
        top_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        
        for idx in top_indices:
            if len(recommendations) >= request.num_recommendations:
                break
            
            assessment = self.assessments_cache[idx]
            similarity = float(similarities[idx])
            
            # Apply filters
            if request.remote_testing_required and not assessment.get('remote_testing', False):
                continue
            
            if request.max_duration and assessment.get('duration') and assessment.get('duration', 0) > request.max_duration:
                continue
            
            if request.language:
                languages = ['English']
                if request.language not in languages:
                    continue
            
            # Skip very low similarity scores
            if similarity < 0.01:
                continue
            
            # Calculate additional scores
            skill_match = self._calculate_skill_match(request, assessment)
            industry_match = self._calculate_industry_match(request, assessment)
            
            # Combined score
            total_score = (similarity * 0.5) + (skill_match * 0.3) + (industry_match * 0.2)
            
            assessment_response = self._db_to_response(assessment)
            
            score = RecommendationScore(
                total_score=total_score,
                relevance_score=similarity,
                skill_match_score=skill_match,
                industry_match_score=industry_match,
                explanation=f"TF-IDF similarity: {similarity:.2f}, Skill match: {skill_match:.2f}"
            )
            
            recommendations.append(RecommendationItem(
                assessment=assessment_response,
                score=score,
                rank=len(recommendations) + 1
            ))
        
        log.info(f"NLP returned {len(recommendations)} recommendations")
        return recommendations
    
    def _calculate_skill_match(self, request: RecommendationRequest, assessment: dict) -> float:
        """Calculate skill match score"""
        if not request.required_skills:
            return 0.5
        
        assessment_skills = set()
        required_skills = set(s.lower() for s in request.required_skills)
        
        if not assessment_skills:
            return 0.0
        
        intersection = assessment_skills.intersection(required_skills)
        return len(intersection) / len(required_skills) if required_skills else 0.5
    
    def _calculate_industry_match(self, request: RecommendationRequest, assessment: dict) -> float:
        """Calculate industry match score"""
        if not request.industry:
            return 0.5
        
        assessment_industries = []
        
        if "all industries" in assessment_industries:
            return 1.0
        
        if request.industry.lower() in assessment_industries:
            return 1.0
        
        return 0.0
    
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


