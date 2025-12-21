"""
Quick verification script to check Supabase migration
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

def verify():
    db = get_supabase_client()
    
    # Count total records
    result = db.table('assessment_embeddings').select('id', count='exact').execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    
    print(f"✅ Total records in Supabase: {count}")
    
    # Check sample
    sample = db.table('assessment_embeddings').select('id', 'name', 'job_level').limit(5).execute()
    
    print(f"\n📋 Sample records:")
    for row in sample.data:
        print(f"  - {row['id']}: {row['name']} ({row['job_level']})")
    
    return count

if __name__ == "__main__":
    count = verify()
    sys.exit(0 if count > 400 else 1)
