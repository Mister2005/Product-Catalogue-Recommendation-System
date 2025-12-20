"""
Train Set Evaluation Script
Evaluates the recommendation system on the labeled train set
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.evaluation.evaluation_data import load_train_data
from app.evaluation.recall_evaluator import calculate_mean_recall_at_k, print_evaluation_report
from app.core.config import get_settings
from app.core.logging import log
import httpx


async def evaluate_train_set(api_url: str = "http://localhost:8000"):
    """
    Evaluate recommendation system on train set
    
    Args:
        api_url: Base URL of the API
    """
    print("="*80)
    print("TRAIN SET EVALUATION")
    print("="*80)
    
    # Load train data
    print("\nLoading train data...")
    train_data = load_train_data()
    print(f"Loaded {len(train_data)} labeled queries")
    
    # Generate predictions for each query
    print("\nGenerating recommendations...")
    predictions = {}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, (query, relevant_urls) in enumerate(train_data.items(), 1):
            print(f"\n[{idx}/{len(train_data)}] Query: {query[:80]}...")
            print(f"  Ground truth: {len(relevant_urls)} relevant assessments")
            
            try:
                # Call recommendation API
                response = await client.post(
                    f"{api_url}/recommend",
                    json={"query": query}
                )
                response.raise_for_status()
                
                # Extract URLs from response
                data = response.json()
                recommended_urls = [rec["assessment_url"] for rec in data["recommendations"]]
                predictions[query] = recommended_urls
                
                print(f"  Recommended: {len(recommended_urls)} assessments")
                
            except Exception as e:
                log.error(f"Error getting recommendations for query: {e}")
                predictions[query] = []
                print(f"  ERROR: {str(e)}")
    
    # Calculate and print evaluation metrics
    print("\n")
    print_evaluation_report(train_data, predictions)
    
    # Calculate overall Mean Recall@10
    mean_recall_10 = calculate_mean_recall_at_k(train_data, predictions, k=10)
    
    return mean_recall_10


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate on train set")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    mean_recall = asyncio.run(evaluate_train_set(args.api_url))
    
    # Exit with appropriate code
    if mean_recall >= 0.7:
        print(f"\n✅ SUCCESS: Mean Recall@10 = {mean_recall:.4f} >= 0.7")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Mean Recall@10 = {mean_recall:.4f} < 0.7")
        sys.exit(1)
