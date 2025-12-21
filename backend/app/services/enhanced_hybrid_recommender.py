from typing import List, Dict, Any, Optional
import logging
from app.services.rag_recommender_v2 import RAGRecommender

log = logging.getLogger(__name__)

class EnhancedHybridRecommender:
    """
    Service to generate recommendations.
    Currently prioritizes RAG (Retrieval-Augmented Generation) for PDF compliance.
    """
    def __init__(self):
        self.rag_recommender = RAGRecommender()
        log.info("Initialized EnhancedHybridRecommender with RAG engine.")

    def recommend(self, query: str, n_results: int = 10) -> Dict[str, Any]:
        """
        Get recommendations for a user query.
        Returns a dict matching the API response structure.
        """
        log.info(f"Processing recommendation request for query: {query}")
        
        # 1. Get logic from RAG
        results = self.rag_recommender.recommend(query, n_results=n_results)
        
        # 2. (Optional) Re-ranking or filtering could go here.
        # For now, return direct results.
        
        # 3. Format strictly for API model
        # The RAGRecommender already returns dicts matching columns, 
        # but we need to ensure the key is 'recommended_assessments'
        
        return {
            "recommended_assessments": results
        }

    def chat(self, message: str, history: List[Dict[str, str]] = []) -> str:
        """
        Chat with AI.
        """
        return self.rag_recommender.chat(message, history)
