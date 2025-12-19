"""
Retrieval evaluation module
Measures retrieval quality using Precision@K, Recall@K, and MRR metrics
"""
import numpy as np
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class RetrievalEvaluator:
    """Evaluates retrieval quality for the recommendation system"""
    
    def __init__(self, test_cases: List[Dict[str, Any]]):
        """
        Initialize evaluator with test cases
        
        Args:
            test_cases: List of test cases with queries and expected results
        """
        self.test_cases = test_cases
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        """
        Calculate Precision@K
        
        Args:
            retrieved: List of retrieved item IDs (in order)
            relevant: Set of relevant item IDs
            k: Number of top results to consider
            
        Returns:
            Precision@K score
        """
        if k == 0 or not retrieved:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_in_top_k = sum(1 for item in top_k if item in relevant)
        
        return relevant_in_top_k / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        """
        Calculate Recall@K
        
        Args:
            retrieved: List of retrieved item IDs (in order)
            relevant: Set of relevant item IDs
            k: Number of top results to consider
            
        Returns:
            Recall@K score
        """
        if not relevant or not retrieved:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_in_top_k = sum(1 for item in top_k if item in relevant)
        
        return relevant_in_top_k / len(relevant)
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR)
        
        Args:
            retrieved: List of retrieved item IDs (in order)
            relevant: Set of relevant item IDs
            
        Returns:
            MRR score
        """
        for i, item in enumerate(retrieved, 1):
            if item in relevant:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def average_precision(retrieved: List[str], relevant: Set[str]) -> float:
        """
        Calculate Average Precision
        
        Args:
            retrieved: List of retrieved item IDs (in order)
            relevant: Set of relevant item IDs
            
        Returns:
            Average Precision score
        """
        if not relevant:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for i, item in enumerate(retrieved, 1):
            if item in relevant:
                relevant_count += 1
                precision = relevant_count / i
                precisions.append(precision)
        
        if not precisions:
            return 0.0
        
        return sum(precisions) / len(relevant)
    
    def evaluate_single_query(self, retrieved: List[str], relevant: List[str], k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Evaluate a single query
        
        Args:
            retrieved: List of retrieved item IDs
            relevant: List of relevant item IDs
            k_values: List of K values to evaluate
            
        Returns:
            Dictionary with metrics
        """
        relevant_set = set(relevant)
        
        metrics = {
            'mrr': self.mean_reciprocal_rank(retrieved, relevant_set),
            'average_precision': self.average_precision(retrieved, relevant_set)
        }
        
        for k in k_values:
            metrics[f'precision@{k}'] = self.precision_at_k(retrieved, relevant_set, k)
            metrics[f'recall@{k}'] = self.recall_at_k(retrieved, relevant_set, k)
        
        return metrics
    
    def evaluate_all(self, retrieval_function, k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Evaluate all test cases
        
        Args:
            retrieval_function: Function that takes a query dict and returns list of retrieved IDs
            k_values: List of K values to evaluate
            
        Returns:
            Aggregated evaluation metrics
        """
        all_metrics = []
        
        for test_case in self.test_cases:
            query = test_case['query']
            expected_ids = test_case.get('expected_ids', [])
            
            # Get retrieved results
            try:
                retrieved_ids = retrieval_function(query)
            except Exception as e:
                logger.error(f"Error retrieving results for query '{query}': {e}")
                continue
            
            # Evaluate
            metrics = self.evaluate_single_query(retrieved_ids, expected_ids, k_values)
            metrics['query'] = query
            all_metrics.append(metrics)
        
        # Aggregate metrics
        if not all_metrics:
            return {'status': 'FAILED', 'message': 'No successful retrievals'}
        
        aggregated = {
            'num_queries': len(all_metrics),
            'mrr': np.mean([m['mrr'] for m in all_metrics]),
            'map': np.mean([m['average_precision'] for m in all_metrics])
        }
        
        for k in k_values:
            aggregated[f'precision@{k}'] = np.mean([m[f'precision@{k}'] for m in all_metrics])
            aggregated[f'recall@{k}'] = np.mean([m[f'recall@{k}'] for m in all_metrics])
        
        # Determine status
        precision_10 = aggregated.get('precision@10', 0)
        recall_10 = aggregated.get('recall@10', 0)
        mrr = aggregated['mrr']
        
        if precision_10 >= 0.8 and recall_10 >= 0.7 and mrr >= 0.85:
            status = 'PASSED'
        elif precision_10 >= 0.6 and recall_10 >= 0.5 and mrr >= 0.70:
            status = 'WARNING'
        else:
            status = 'FAILED'
        
        aggregated['status'] = status
        aggregated['individual_results'] = all_metrics
        
        return aggregated
    
    def print_report(self, results: Dict[str, Any]):
        """Print formatted evaluation report"""
        print("\n" + "="*70)
        print("🔍 RETRIEVAL EVALUATION REPORT")
        print("="*70)
        
        print(f"\n🎯 Status: {results['status']}")
        print(f"📊 Queries Evaluated: {results['num_queries']}")
        
        print("\n" + "-"*70)
        print("AGGREGATE METRICS")
        print("-"*70)
        print(f"Mean Reciprocal Rank (MRR): {results['mrr']:.4f}")
        print(f"Mean Average Precision (MAP): {results['map']:.4f}")
        
        for key in sorted(results.keys()):
            if key.startswith('precision@'):
                k = key.split('@')[1]
                print(f"Precision@{k}: {results[key]:.4f}")
        
        for key in sorted(results.keys()):
            if key.startswith('recall@'):
                k = key.split('@')[1]
                print(f"Recall@{k}: {results[key]:.4f}")
        
        print("\n" + "="*70 + "\n")


# Test data for evaluation
TEST_QUERIES = [
    {
        'query': 'Python programming assessment',
        'expected_ids': ['python_programming', 'dotnet_framework_45', 'java_programming'],
        'job_family': 'Technology'
    },
    {
        'query': 'Customer service representative',
        'expected_ids': ['customer_service_rep', 'bilingual_spanish_reservation_agent', 'situational_judgment'],
        'job_family': 'Customer Service'
    },
    {
        'query': 'Software engineer technical skills',
        'expected_ids': ['python_programming', 'javascript', 'sql_database', 'cognitive_ability_test'],
        'job_family': 'Technology'
    },
    {
        'query': 'Accounting clerk bookkeeping',
        'expected_ids': ['bookkeeping_clerk_short', 'accounts_payable', 'accounts_receivable', 'microsoft_excel'],
        'job_family': 'Finance'
    },
    {
        'query': 'Sales manager leadership',
        'expected_ids': ['sales_representative', 'account_manager_solution', 'branch_manager_short', 'personality_assessment'],
        'job_family': 'Sales'
    },
    {
        'query': 'Microsoft Office skills',
        'expected_ids': ['microsoft_excel', 'microsoft_word', 'microsoft_powerpoint', 'typing_speed'],
        'job_family': 'Administrative'
    },
    {
        'query': 'Financial analysis investment',
        'expected_ids': ['financial_analysis', 'accounts_receivable', 'cognitive_ability_test'],
        'job_family': 'Finance'
    },
    {
        'query': 'Entry level cashier retail',
        'expected_ids': ['cashier_solution', 'customer_service_rep', 'personality_assessment'],
        'job_family': 'Retail'
    },
    {
        'query': 'Java web development',
        'expected_ids': ['java_programming', 'javascript', 'sql_database', 'dotnet_mvc'],
        'job_family': 'Technology'
    },
    {
        'query': 'Bank operations supervisor',
        'expected_ids': ['bank_operations_supervisor_short', 'branch_manager_short', 'situational_judgment'],
        'job_family': 'Banking'
    }
]


def main():
    """Example usage"""
    evaluator = RetrievalEvaluator(TEST_QUERIES)
    
    # Example retrieval function (replace with actual implementation)
    def mock_retrieval(query):
        # This would be replaced with actual RAG/NLP retrieval
        return ['python_programming', 'javascript', 'sql_database', 'cognitive_ability_test', 'personality_assessment']
    
    results = evaluator.evaluate_all(mock_retrieval)
    evaluator.print_report(results)
    
    return results


if __name__ == "__main__":
    main()
