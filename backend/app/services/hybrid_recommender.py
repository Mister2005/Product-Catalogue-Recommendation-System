"""
Hybrid recommendation engine combining multiple approaches
"""
from typing import List, Dict
from collections import defaultdict

from app.models.schemas import RecommendationRequest, RecommendationItem, RecommendationScore
from app.services.rag_recommender import RAGRecommender
from app.services.nlp_recommender import NLPRecommender
from app.services.clustering_recommender import ClusteringRecommender
from app.services.gemini_recommender import GeminiRecommender
from app.core.logging import log


class HybridRecommender:
    """
    Hybrid recommender that combines multiple recommendation strategies
    LinkedIn-style intelligent recommendation system
    """
    
    def __init__(self, rag_recommender=None, nlp_recommender=None, clustering_recommender=None, gemini_recommender=None):
        """Initialize hybrid recommender with pre-initialized engines"""
        self.rag_recommender = rag_recommender or RAGRecommender()
        self.nlp_recommender = nlp_recommender or NLPRecommender()
        self.clustering_recommender = clustering_recommender or ClusteringRecommender()
        self.gemini_recommender = gemini_recommender or GeminiRecommender()
        
        # Dynamic weights based on engine availability and performance
        self.base_weights = {
            "rag": 0.40,      # Semantic search - most important
            "nlp": 0.30,      # Text matching - reliable fallback
            "clustering": 0.20,  # Pattern recognition
            "gemini": 0.10    # AI insights - bonus
        }
    
    async def recommend(
        self, 
        request: RecommendationRequest, 
        db
    ) -> List[RecommendationItem]:
        """
        Generate hybrid recommendations
        
        Args:
            request: Recommendation request
            db: Database session
            
        Returns:
            Combined and re-ranked recommendations
        """
        log.info(f"Hybrid recommendation for: {request.dict()}")
        
        # Get recommendations from each engine
        recommendations_by_engine = {}
        
        # RAG recommendations
        try:
            rag_recs = await self.rag_recommender.recommend(request, db)
            recommendations_by_engine["rag"] = rag_recs
            log.info(f"RAG contributed {len(rag_recs)} recommendations")
        except Exception as e:
            log.error(f"RAG recommender error: {e}")
            recommendations_by_engine["rag"] = []
        
        # NLP recommendations
        try:
            nlp_recs = await self.nlp_recommender.recommend(request, db)
            recommendations_by_engine["nlp"] = nlp_recs
            log.info(f"NLP contributed {len(nlp_recs)} recommendations")
        except Exception as e:
            log.error(f"NLP recommender error: {e}")
            recommendations_by_engine["nlp"] = []
        
        # Clustering recommendations
        try:
            clustering_recs = await self.clustering_recommender.recommend(request, db)
            recommendations_by_engine["clustering"] = clustering_recs
            log.info(f"Clustering contributed {len(clustering_recs)} recommendations")
        except Exception as e:
            log.error(f"Clustering recommender error: {e}")
            recommendations_by_engine["clustering"] = []
        
        # Gemini recommendations (if available)
        try:
            if self.gemini_recommender.model:
                gemini_recs = await self.gemini_recommender.recommend(request, db)
                recommendations_by_engine["gemini"] = gemini_recs
                log.info(f"Gemini contributed {len(gemini_recs)} recommendations")
            else:
                recommendations_by_engine["gemini"] = []
        except Exception as e:
            log.error(f"Gemini recommender error: {e}")
            recommendations_by_engine["gemini"] = []
        
        # Combine recommendations
        combined = self._combine_recommendations(recommendations_by_engine, request.num_recommendations)
        
        log.info(f"Hybrid returned {len(combined)} recommendations")
        return combined
    
    def _combine_recommendations(
        self, 
        recommendations_by_engine: Dict[str, List[RecommendationItem]], 
        num_results: int
    ) -> List[RecommendationItem]:
        """
        Intelligently combine and re-rank recommendations from multiple engines
        Uses dynamic weighting based on which engines contributed results
        """
        # Calculate active engines and adjust weights dynamically
        active_engines = {k: v for k, v in recommendations_by_engine.items() if v}
        
        if not active_engines:
            log.warning("No recommendations from any engine")
            return []
        
        # Redistribute weights among active engines
        total_base_weight = sum(self.base_weights.get(engine, 0.25) for engine in active_engines.keys())
        adjusted_weights = {
            engine: self.base_weights.get(engine, 0.25) / total_base_weight
            for engine in active_engines.keys()
        }
        
        log.info(f"Active engines: {list(active_engines.keys())}, Adjusted weights: {adjusted_weights}")
        
        # Collect scores for each assessment
        assessment_scores = defaultdict(lambda: {
            "total_score": 0.0,
            "count": 0,
            "engines": [],
            "assessment": None,
            "score_details": {},
            "max_individual_score": 0.0
        })
        
        for engine, recommendations in active_engines.items():
            weight = adjusted_weights[engine]
            
            for rec in recommendations:
                assessment_id = rec.assessment.id
                
                # Store assessment object
                if assessment_scores[assessment_id]["assessment"] is None:
                    assessment_scores[assessment_id]["assessment"] = rec.assessment
                
                # Weighted score
                weighted_score = rec.score.total_score * weight
                assessment_scores[assessment_id]["total_score"] += weighted_score
                assessment_scores[assessment_id]["count"] += 1
                assessment_scores[assessment_id]["engines"].append(engine)
                assessment_scores[assessment_id]["score_details"][engine] = rec.score.total_score
                assessment_scores[assessment_id]["max_individual_score"] = max(
                    assessment_scores[assessment_id]["max_individual_score"],
                    rec.score.total_score
                )
        
        # Create final recommendations with LinkedIn-style scoring
        final_recommendations = []
        
        for assessment_id, data in assessment_scores.items():
            # Multi-engine consensus bonus (like LinkedIn's collaborative signals)
            consensus_bonus = 0.15 * min(data["count"] - 1, 2)  # Cap bonus at 2 extra engines
            
            # High individual score bonus (one engine really confident)
            confidence_bonus = 0.1 if data["max_individual_score"] > 0.8 else 0
            
            # Calculate final score with bonuses
            final_score = data["total_score"] + consensus_bonus + confidence_bonus
            
            # Create detailed explanation
            engines_str = ", ".join(data["engines"])
            engine_scores = ", ".join([f"{e}:{s:.2f}" for e, s in data["score_details"].items()])
            explanation = f"🎯 Matched by {len(data['engines'])} engine(s): {engines_str} | Scores: [{engine_scores}] | Consensus: {final_score:.2f}"
            
            # Confidence based on how many engines agreed
            confidence_score = min(1.0, (data["count"] / len(active_engines)) + 0.2)
            
            score = RecommendationScore(
                total_score=final_score,
                relevance_score=data["total_score"],
                confidence=confidence_score,
                explanation=explanation
            )
            
            final_recommendations.append(RecommendationItem(
                assessment=data["assessment"],
                score=score,
                rank=0  # Will be updated after sorting
            ))
        
        # Sort by total score (with bonuses)
        final_recommendations.sort(key=lambda x: x.score.total_score, reverse=True)
        
        # Update ranks and limit results
        final_recommendations = final_recommendations[:num_results]
        for idx, rec in enumerate(final_recommendations):
            rec.rank = idx + 1
        
        log.info(f"Combined {len(assessment_scores)} unique assessments into {len(final_recommendations)} final recommendations")
        
        return final_recommendations
