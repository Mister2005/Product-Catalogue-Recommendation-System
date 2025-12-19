"""
Recommendation evaluation module
Measures recommendation quality using NDCG, MAP, and Hit Rate metrics
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class RecommendationEvaluator:
    """Evaluates recommendation quality for the system"""
    
    def __init__(self, test_cases: List[Dict[str, Any]]):
        """
        Initialize evaluator with test cases
        
        Args:
            test_cases: List of test cases with requests and expected recommendations
        """
        self.test_cases = test_cases
    
    @staticmethod
    def dcg_at_k(relevances: List[float], k: int) -> float:
        """
        Calculate Discounted Cumulative Gain at K
        
        Args:
            relevances: List of relevance scores (in order of recommendations)
            k: Number of top results to consider
            
        Returns:
            DCG@K score
        """
        relevances = relevances[:k]
        if not relevances:
            return 0.0
        
        return sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))
    
    @staticmethod
    def ndcg_at_k(relevances: List[float], k: int) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at K
        
        Args:
            relevances: List of relevance scores (in order of recommendations)
            k: Number of top results to consider
            
        Returns:
            NDCG@K score
        """
        dcg = RecommendationEvaluator.dcg_at_k(relevances, k)
        
        # Ideal DCG (sorted by relevance)
        ideal_relevances = sorted(relevances, reverse=True)
        idcg = RecommendationEvaluator.dcg_at_k(ideal_relevances, k)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def hit_rate_at_k(recommended_ids: List[str], relevant_ids: List[str], k: int) -> float:
        """
        Calculate Hit Rate at K (whether any relevant item is in top K)
        
        Args:
            recommended_ids: List of recommended item IDs
            relevant_ids: List of relevant item IDs
            k: Number of top results to consider
            
        Returns:
            1.0 if hit, 0.0 otherwise
        """
        top_k = set(recommended_ids[:k])
        relevant_set = set(relevant_ids)
        
        return 1.0 if top_k.intersection(relevant_set) else 0.0
    
    @staticmethod
    def average_precision(recommended_ids: List[str], relevant_dict: Dict[str, float]) -> float:
        """
        Calculate Average Precision
        
        Args:
            recommended_ids: List of recommended item IDs (in order)
            relevant_dict: Dictionary mapping item IDs to relevance scores
            
        Returns:
            Average Precision score
        """
        if not relevant_dict:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for i, item_id in enumerate(recommended_ids, 1):
            if item_id in relevant_dict and relevant_dict[item_id] > 0:
                relevant_count += 1
                precision = relevant_count / i
                precisions.append(precision)
        
        if not precisions:
            return 0.0
        
        return sum(precisions) / len(relevant_dict)
    
    def evaluate_single_recommendation(
        self,
        recommended_ids: List[str],
        expected_recommendations: List[Dict[str, Any]],
        k_values: List[int] = [5, 10]
    ) -> Dict[str, Any]:
        """
        Evaluate a single recommendation result
        
        Args:
            recommended_ids: List of recommended item IDs
            expected_recommendations: List of dicts with 'id' and 'relevance' keys
            k_values: List of K values to evaluate
            
        Returns:
            Dictionary with metrics
        """
        # Create relevance mapping
        relevance_dict = {item['id']: item['relevance'] for item in expected_recommendations}
        relevant_ids = list(relevance_dict.keys())
        
        # Get relevance scores for recommended items
        relevances = [relevance_dict.get(item_id, 0.0) for item_id in recommended_ids]
        
        metrics = {
            'average_precision': self.average_precision(recommended_ids, relevance_dict)
        }
        
        for k in k_values:
            metrics[f'ndcg@{k}'] = self.ndcg_at_k(relevances, k)
            metrics[f'hit_rate@{k}'] = self.hit_rate_at_k(recommended_ids, relevant_ids, k)
        
        return metrics
    
    def evaluate_all(
        self,
        recommendation_function,
        k_values: List[int] = [5, 10]
    ) -> Dict[str, Any]:
        """
        Evaluate all test cases
        
        Args:
            recommendation_function: Function that takes a request dict and returns list of recommended IDs
            k_values: List of K values to evaluate
            
        Returns:
            Aggregated evaluation metrics
        """
        all_metrics = []
        
        for test_case in self.test_cases:
            request = test_case['request']
            expected = test_case['expected_recommendations']
            
            # Get recommendations
            try:
                recommended_ids = recommendation_function(request)
            except Exception as e:
                logger.error(f"Error getting recommendations for {request.get('job_title')}: {e}")
                continue
            
            # Evaluate
            metrics = self.evaluate_single_recommendation(recommended_ids, expected, k_values)
            metrics['job_title'] = request.get('job_title', 'Unknown')
            all_metrics.append(metrics)
        
        # Aggregate metrics
        if not all_metrics:
            return {'status': 'FAILED', 'message': 'No successful recommendations'}
        
        aggregated = {
            'num_test_cases': len(all_metrics),
            'map': np.mean([m['average_precision'] for m in all_metrics])
        }
        
        for k in k_values:
            aggregated[f'ndcg@{k}'] = np.mean([m[f'ndcg@{k}'] for m in all_metrics])
            aggregated[f'hit_rate@{k}'] = np.mean([m[f'hit_rate@{k}'] for m in all_metrics])
        
        # Determine status
        ndcg_10 = aggregated.get('ndcg@10', 0)
        map_score = aggregated['map']
        hit_rate_5 = aggregated.get('hit_rate@5', 0)
        
        if ndcg_10 >= 0.75 and map_score >= 0.70 and hit_rate_5 >= 0.85:
            status = 'PASSED'
        elif ndcg_10 >= 0.60 and map_score >= 0.55 and hit_rate_5 >= 0.70:
            status = 'WARNING'
        else:
            status = 'FAILED'
        
        aggregated['status'] = status
        aggregated['individual_results'] = all_metrics
        
        return aggregated
    
    def print_report(self, results: Dict[str, Any]):
        """Print formatted evaluation report"""
        print("\n" + "="*70)
        print("🎯 RECOMMENDATION EVALUATION REPORT")
        print("="*70)
        
        print(f"\n🎯 Status: {results['status']}")
        print(f"📊 Test Cases Evaluated: {results['num_test_cases']}")
        
        print("\n" + "-"*70)
        print("AGGREGATE METRICS")
        print("-"*70)
        print(f"Mean Average Precision (MAP): {results['map']:.4f}")
        
        for key in sorted(results.keys()):
            if key.startswith('ndcg@'):
                k = key.split('@')[1]
                print(f"NDCG@{k}: {results[key]:.4f}")
        
        for key in sorted(results.keys()):
            if key.startswith('hit_rate@'):
                k = key.split('@')[1]
                print(f"Hit Rate@{k}: {results[key]:.4f}")
        
        print("\n" + "="*70 + "\n")


# Test cases for evaluation
EVALUATION_CASES = [
    {
        "request": {
            "job_title": "Software Engineer",
            "required_skills": ["Python", "JavaScript"],
            "job_family": "Technology",
            "job_level": "Intermediate"
        },
        "expected_recommendations": [
            {"id": "python_programming", "relevance": 1.0},
            {"id": "javascript", "relevance": 1.0},
            {"id": "cognitive_ability_test", "relevance": 0.8},
            {"id": "sql_database", "relevance": 0.7},
            {"id": "personality_assessment", "relevance": 0.6}
        ]
    },
    {
        "request": {
            "job_title": "Customer Service Representative",
            "required_skills": ["Communication", "Problem Solving"],
            "job_family": "Customer Service",
            "job_level": "Entry Level"
        },
        "expected_recommendations": [
            {"id": "customer_service_rep", "relevance": 1.0},
            {"id": "situational_judgment", "relevance": 0.9},
            {"id": "personality_assessment", "relevance": 0.8},
            {"id": "cognitive_ability_test", "relevance": 0.6}
        ]
    },
    {
        "request": {
            "job_title": "Accountant",
            "required_skills": ["Bookkeeping", "Excel", "Attention to Detail"],
            "job_family": "Finance",
            "job_level": "Intermediate"
        },
        "expected_recommendations": [
            {"id": "bookkeeping_clerk_short", "relevance": 1.0},
            {"id": "microsoft_excel", "relevance": 0.9},
            {"id": "accounts_payable", "relevance": 0.8},
            {"id": "accounts_receivable", "relevance": 0.8},
            {"id": "cognitive_ability_test", "relevance": 0.7}
        ]
    },
    {
        "request": {
            "job_title": "Sales Manager",
            "required_skills": ["Leadership", "Sales", "Communication"],
            "job_family": "Sales",
            "job_level": "Manager"
        },
        "expected_recommendations": [
            {"id": "sales_representative", "relevance": 1.0},
            {"id": "account_manager_solution", "relevance": 0.9},
            {"id": "personality_assessment", "relevance": 0.8},
            {"id": "situational_judgment", "relevance": 0.8},
            {"id": "cognitive_ability_test", "relevance": 0.7}
        ]
    },
    {
        "request": {
            "job_title": "Administrative Assistant",
            "required_skills": ["Microsoft Office", "Organization", "Communication"],
            "job_family": "Administrative",
            "job_level": "Entry Level"
        },
        "expected_recommendations": [
            {"id": "administrative_professional_short", "relevance": 1.0},
            {"id": "microsoft_excel", "relevance": 0.9},
            {"id": "microsoft_word", "relevance": 0.9},
            {"id": "typing_speed", "relevance": 0.8},
            {"id": "personality_assessment", "relevance": 0.7}
        ]
    }
]


def main():
    """Example usage"""
    evaluator = RecommendationEvaluator(EVALUATION_CASES)
    
    # Example recommendation function (replace with actual implementation)
    def mock_recommendation(request):
        # This would be replaced with actual recommendation engine
        return ['python_programming', 'javascript', 'cognitive_ability_test', 'personality_assessment', 'sql_database']
    
    results = evaluator.evaluate_all(mock_recommendation)
    evaluator.print_report(results)
    
    return results


if __name__ == "__main__":
    main()
