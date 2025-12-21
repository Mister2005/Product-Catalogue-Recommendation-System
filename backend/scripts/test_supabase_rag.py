"""
Quick test of Supabase-based RAG recommender
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from root directory (parent of backend)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

print("Testing RAG Recommender with Supabase...")
print(f"VECTOR_DB_TYPE = {os.getenv('VECTOR_DB_TYPE', 'not set')}")

try:
    from app.services.rag_recommender_v2 import RAGRecommender
    print("✅ Import successful")
    
    print("\nInitializing RAG recommender...")
    rag = RAGRecommender()
    print("✅ RAG recommender initialized")
    
    print("\nTesting recommendation...")
    results = rag.recommend('Python developer internship', n_results=3)
    
    print(f"\n✅ Got {len(results)} recommendations:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['name']} ({r.get('job_level', 'N/A')})")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
