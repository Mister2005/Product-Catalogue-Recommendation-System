"""
Mean Recall@K evaluator for SHL Assignment
Implements the evaluation metric specified in the assignment
"""
from typing import List, Dict


def calculate_recall_at_k(relevant_urls: List[str], recommended_urls: List[str], k: int) -> float:
    """
    Calculate Recall@K for a single query
    
    Recall@K = (Number of relevant assessments in top K) / (Total relevant assessments for the query)
    
    Args:
        relevant_urls: List of ground truth relevant assessment URLs
        recommended_urls: List of recommended assessment URLs (ordered by relevance)
        k: Number of top recommendations to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_urls:
        return 0.0
    
    # Get top K recommendations
    top_k = recommended_urls[:k]
    
    # Count how many relevant URLs are in top K
    relevant_in_top_k = len(set(top_k) & set(relevant_urls))
    
    # Calculate recall
    total_relevant = len(relevant_urls)
    recall = relevant_in_top_k / total_relevant
    
    return recall


def calculate_mean_recall_at_k(
    ground_truth: Dict[str, List[str]], 
    predictions: Dict[str, List[str]], 
    k: int = 10
) -> float:
    """
    Calculate Mean Recall@K across all queries
    
    Mean Recall@K = (1/N) * Σ Recall@K_i
    where N is the total number of test queries
    
    Args:
        ground_truth: Dictionary mapping query to list of relevant URLs
        predictions: Dictionary mapping query to list of predicted URLs
        k: Number of top recommendations to consider (default: 10)
        
    Returns:
        Mean Recall@K score (0.0 to 1.0)
    """
    if not ground_truth:
        return 0.0
    
    recalls = []
    
    for query, relevant_urls in ground_truth.items():
        recommended_urls = predictions.get(query, [])
        recall = calculate_recall_at_k(relevant_urls, recommended_urls, k)
        recalls.append(recall)
    
    # Calculate mean
    mean_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    return mean_recall


def calculate_metrics_per_query(
    ground_truth: Dict[str, List[str]], 
    predictions: Dict[str, List[str]]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate Recall@K metrics for each query at K=1, 5, 10
    
    Args:
        ground_truth: Dictionary mapping query to list of relevant URLs
        predictions: Dictionary mapping query to list of predicted URLs
        
    Returns:
        Dictionary mapping query to metrics dict
        Format: {query: {"recall@1": 0.5, "recall@5": 0.8, "recall@10": 1.0}}
    """
    results = {}
    
    for query, relevant_urls in ground_truth.items():
        recommended_urls = predictions.get(query, [])
        
        results[query] = {
            "recall@1": calculate_recall_at_k(relevant_urls, recommended_urls, 1),
            "recall@5": calculate_recall_at_k(relevant_urls, recommended_urls, 5),
            "recall@10": calculate_recall_at_k(relevant_urls, recommended_urls, 10),
            "num_relevant": len(relevant_urls),
            "num_recommended": len(recommended_urls)
        }
    
    return results


def print_evaluation_report(
    ground_truth: Dict[str, List[str]], 
    predictions: Dict[str, List[str]]
):
    """
    Print detailed evaluation report
    
    Args:
        ground_truth: Dictionary mapping query to list of relevant URLs
        predictions: Dictionary mapping query to list of predicted URLs
    """
    print("="*80)
    print("EVALUATION REPORT - Mean Recall@K")
    print("="*80)
    
    # Calculate overall metrics
    mean_recall_1 = calculate_mean_recall_at_k(ground_truth, predictions, k=1)
    mean_recall_5 = calculate_mean_recall_at_k(ground_truth, predictions, k=5)
    mean_recall_10 = calculate_mean_recall_at_k(ground_truth, predictions, k=10)
    
    print(f"\nOverall Metrics:")
    print(f"  Mean Recall@1:  {mean_recall_1:.4f}")
    print(f"  Mean Recall@5:  {mean_recall_5:.4f}")
    print(f"  Mean Recall@10: {mean_recall_10:.4f}")
    
    # Per-query metrics
    per_query = calculate_metrics_per_query(ground_truth, predictions)
    
    print(f"\nPer-Query Metrics:")
    print(f"{'Query':<50} {'R@1':<8} {'R@5':<8} {'R@10':<8} {'Relevant':<10}")
    print("-"*80)
    
    for query, metrics in per_query.items():
        query_short = query[:47] + "..." if len(query) > 50 else query
        print(f"{query_short:<50} {metrics['recall@1']:<8.3f} {metrics['recall@5']:<8.3f} "
              f"{metrics['recall@10']:<8.3f} {metrics['num_relevant']:<10}")
    
    print("="*80)
    
    # Target check
    if mean_recall_10 >= 0.7:
        print(f"✅ PASSED: Mean Recall@10 ({mean_recall_10:.4f}) >= 0.7 target")
    else:
        print(f"❌ FAILED: Mean Recall@10 ({mean_recall_10:.4f}) < 0.7 target")
    
    print("="*80)
