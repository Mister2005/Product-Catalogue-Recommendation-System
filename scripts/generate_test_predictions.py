"""
Test Set Prediction Generation Script
Generates predictions for the unlabeled test set and saves to CSV
"""
import asyncio
import sys
import csv
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.evaluation.evaluation_data import load_test_data
from app.core.logging import log
import httpx


async def generate_test_predictions(
    api_url: str = "http://localhost:8000",
    output_file: str = "test_predictions.csv"
):
    """
    Generate predictions for test set and save to CSV
    
    Args:
        api_url: Base URL of the API
        output_file: Output CSV file path
    """
    print("="*80)
    print("TEST SET PREDICTION GENERATION")
    print("="*80)
    
    # Load test data
    print("\nLoading test data...")
    test_queries = load_test_data()
    print(f"Loaded {len(test_queries)} test queries")
    
    # Generate predictions for each query
    print("\nGenerating recommendations...")
    all_predictions = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, query in enumerate(test_queries, 1):
            print(f"\n[{idx}/{len(test_queries)}] Query: {query[:80]}...")
            
            try:
                # Call recommendation API
                response = await client.post(
                    f"{api_url}/recommend",
                    json={"query": query}
                )
                response.raise_for_status()
                
                # Extract URLs from response
                data = response.json()
                recommendations = data["recommendations"]
                
                print(f"  Recommended: {len(recommendations)} assessments")
                
                # Add to predictions list
                for rec in recommendations:
                    all_predictions.append({
                        "Query": query,
                        "Assessment_url": rec["assessment_url"]
                    })
                
            except Exception as e:
                log.error(f"Error getting recommendations for query: {e}")
                print(f"  ERROR: {str(e)}")
                # Add at least one empty prediction to maintain format
                all_predictions.append({
                    "Query": query,
                    "Assessment_url": ""
                })
    
    # Save to CSV
    print(f"\nSaving predictions to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Query", "Assessment_url"])
        writer.writeheader()
        writer.writerows(all_predictions)
    
    print(f"✅ Saved {len(all_predictions)} predictions to {output_file}")
    print("\nCSV Format:")
    print("  Query,Assessment_url")
    print("  Query 1,Recommendation 1 (URL)")
    print("  Query 1,Recommendation 2 (URL)")
    print("  ...")
    print("="*80)
    
    return output_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test set predictions")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output",
        default="test_predictions.csv",
        help="Output CSV file (default: test_predictions.csv)"
    )
    
    args = parser.parse_args()
    
    # Run prediction generation
    output_file = asyncio.run(generate_test_predictions(args.api_url, args.output))
    
    print(f"\n✅ SUCCESS: Predictions saved to {output_file}")
    print(f"📋 Submit this file as part of your assignment")
