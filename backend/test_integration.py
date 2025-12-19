"""
Integration Test Script
Tests all backend components before deployment
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

async def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n" + "="*60)
    print("Testing Supabase Connection...")
    print("="*60)
    
    try:
        from app.core.database import get_supabase_client
        
        supabase = get_supabase_client()
        response = supabase.table('assessments').select('id, name').limit(5).execute()
        
        print(f"✅ Connected to Supabase")
        print(f"✅ Found {len(response.data)} assessments")
        
        if response.data:
            print(f"\nSample assessments:")
            for i, item in enumerate(response.data[:3], 1):
                print(f"  {i}. {item.get('name', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


async def test_embedding_service():
    """Test embedding generation"""
    print("\n" + "="*60)
    print("Testing Embedding Service...")
    print("="*60)
    
    try:
        from app.services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        
        # Test embedding generation
        test_text = "Software Engineer with Python and JavaScript skills"
        embedding = await service.get_embedding(test_text)
        
        print(f"✅ Embedding service initialized")
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   Sample values: {embedding[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ Embedding service failed: {e}")
        print(f"   Make sure HUGGINGFACE_API_KEY is set in .env")
        return False


async def test_recommenders():
    """Test recommendation engines"""
    print("\n" + "="*60)
    print("Testing Recommendation Engines...")
    print("="*60)
    
    results = {}
    
    # Test RAG Recommender
    try:
        from app.services.rag_recommender import RAGRecommender
        recommender = RAGRecommender()
        print("✅ RAG Recommender initialized")
        results['rag'] = True
    except Exception as e:
        print(f"❌ RAG Recommender failed: {e}")
        results['rag'] = False
    
    # Test Gemini Recommender
    try:
        from app.services.gemini_recommender import GeminiRecommender
        recommender = GeminiRecommender()
        print("✅ Gemini Recommender initialized")
        results['gemini'] = True
    except Exception as e:
        print(f"⚠️  Gemini Recommender warning: {e}")
        print("   This is OK if GEMINI_API_KEY is not set")
        results['gemini'] = False
    
    # Test NLP Recommender
    try:
        from app.services.nlp_recommender import NLPRecommender
        recommender = NLPRecommender()
        print("✅ NLP Recommender initialized")
        results['nlp'] = True
    except Exception as e:
        print(f"❌ NLP Recommender failed: {e}")
        results['nlp'] = False
    
    # Test Clustering Recommender
    try:
        from app.services.clustering_recommender import ClusteringRecommender
        recommender = ClusteringRecommender()
        print("✅ Clustering Recommender initialized")
        results['clustering'] = True
    except Exception as e:
        print(f"❌ Clustering Recommender failed: {e}")
        results['clustering'] = False
    
    # Test Hybrid Recommender
    try:
        from app.services.hybrid_recommender import HybridRecommender
        recommender = HybridRecommender()
        print("✅ Hybrid Recommender initialized")
        results['hybrid'] = True
    except Exception as e:
        print(f"❌ Hybrid Recommender failed: {e}")
        results['hybrid'] = False
    
    return all(results.values())


async def test_health_endpoint():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint...")
    print("="*60)
    
    try:
        import httpx
        
        # Start server in background would be complex, so just check if app can be imported
        from app.main import app
        
        print("✅ FastAPI app can be imported")
        print("   To test health endpoint, run:")
        print("   uvicorn app.main:app --reload")
        print("   Then visit: http://localhost:8000/health")
        
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False


async def test_environment_variables():
    """Check required environment variables"""
    print("\n" + "="*60)
    print("Checking Environment Variables...")
    print("="*60)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    }
    
    optional_vars = {
        'HUGGINGFACE_API_KEY': os.getenv('HUGGINGFACE_API_KEY'),
        'REDIS_URL': os.getenv('REDIS_URL'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
    }
    
    all_set = True
    
    print("\nRequired Variables:")
    for var, value in required_vars.items():
        if value:
            print(f"  ✅ {var}: {'*' * 10}...{value[-10:]}")
        else:
            print(f"  ❌ {var}: NOT SET")
            all_set = False
    
    print("\nOptional Variables:")
    for var, value in optional_vars.items():
        if value:
            print(f"  ✅ {var}: {'*' * 10}...{value[-10:]}")
        else:
            print(f"  ⚠️  {var}: NOT SET (optional)")
    
    return all_set


async def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🧪 BACKEND INTEGRATION TESTS")
    print("="*60)
    
    results = {}
    
    # Test environment variables
    results['env'] = await test_environment_variables()
    
    # Test Supabase
    results['supabase'] = await test_supabase_connection()
    
    # Test embedding service
    results['embeddings'] = await test_embedding_service()
    
    # Test recommenders
    results['recommenders'] = await test_recommenders()
    
    # Test health endpoint
    results['health'] = await test_health_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed! Ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Fix issues before deploying.")
    
    print("\n" + "="*60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
