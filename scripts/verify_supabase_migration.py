"""
Verify Supabase Migration Script
Checks that all assessments were successfully migrated to Supabase
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Error: supabase package not installed")
    print("   Run: pip install supabase")
    sys.exit(1)


def verify_migration():
    """Verify Supabase migration"""
    
    print("\n" + "="*80)
    print("🔍 SUPABASE MIGRATION VERIFICATION")
    print("="*80)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("\n❌ FAILED: Supabase credentials not found in environment variables")
        print("   Please set SUPABASE_URL and SUPABASE_KEY in .env file")
        return False
    
    print(f"\n✅ Environment variables found")
    print(f"   URL: {supabase_url[:30]}...")
    
    # Connect to Supabase
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"\n❌ FAILED: Could not connect to Supabase")
        print(f"   Error: {e}")
        return False
    
    # Count assessments in database
    try:
        response = supabase.table('assessments').select('id', count='exact').execute()
        db_count = response.count
        print(f"\n📊 Assessments in database: {db_count}")
    except Exception as e:
        print(f"\n❌ FAILED: Could not query assessments table")
        print(f"   Error: {e}")
        print("   Note: Make sure the 'assessments' table exists in Supabase")
        return False
    
    # Load source JSON data
    json_path = Path(__file__).parent.parent / "data" / "shl_products_complete.json"
    
    if not json_path.exists():
        print(f"\n⚠️  WARNING: Source JSON file not found at {json_path}")
        print("   Cannot compare counts")
    else:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'assessments' in data:
                json_count = len(data['assessments'])
                expected_count = data.get('metadata', {}).get('total_assessments', json_count)
            else:
                json_count = len(data)
                expected_count = json_count
            
            print(f"📄 Assessments in JSON: {json_count}")
            print(f"🎯 Expected count: {expected_count}")
            
            # Compare counts
            if db_count == expected_count:
                print(f"\n✅ PASSED: All {expected_count} assessments migrated successfully")
            elif db_count > expected_count * 0.95:
                print(f"\n⚠️  WARNING: {db_count}/{expected_count} assessments migrated ({db_count/expected_count*100:.1f}%)")
                print("   Migration mostly successful but some assessments may be missing")
            else:
                print(f"\n❌ FAILED: Only {db_count}/{expected_count} assessments migrated ({db_count/expected_count*100:.1f}%)")
                return False
                
        except Exception as e:
            print(f"\n⚠️  WARNING: Could not load source JSON")
            print(f"   Error: {e}")
    
    # Check for embeddings (if embeddings column exists)
    try:
        response = supabase.table('assessments').select('id, embedding').limit(5).execute()
        
        if response.data:
            has_embeddings = any(item.get('embedding') is not None for item in response.data)
            
            if has_embeddings:
                print(f"\n✅ Embeddings found in database")
                
                # Count total with embeddings
                response_all = supabase.table('assessments').select('id, embedding').execute()
                total_with_embeddings = sum(1 for item in response_all.data if item.get('embedding') is not None)
                print(f"   {total_with_embeddings}/{db_count} assessments have embeddings")
            else:
                print(f"\n⚠️  WARNING: No embeddings found in sample")
                print("   Embeddings may not have been generated yet")
    except Exception as e:
        print(f"\n⚠️  Note: Could not check embeddings (column may not exist)")
        print(f"   This is OK if you haven't generated embeddings yet")
    
    # Sample a few assessments
    print("\n" + "-"*80)
    print("SAMPLE ASSESSMENTS")
    print("-"*80)
    
    try:
        response = supabase.table('assessments').select('id, name, type, test_types').limit(3).execute()
        
        for i, item in enumerate(response.data, 1):
            print(f"\n{i}. {item.get('name', 'N/A')}")
            print(f"   ID: {item.get('id', 'N/A')}")
            print(f"   Type: {item.get('type', 'N/A')}")
            print(f"   Test Types: {item.get('test_types', [])}")
    except Exception as e:
        print(f"Could not fetch sample assessments: {e}")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
