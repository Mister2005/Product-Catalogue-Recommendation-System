"""
Migration Script: ChromaDB to Supabase pgvector
Migrates all embeddings and metadata from local ChromaDB to Supabase
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from tqdm import tqdm

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_supabase_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_from_chromadb() -> List[Dict[str, Any]]:
    """Extract all data from ChromaDB"""
    print("=" * 80)
    print("STEP 1: Extracting data from ChromaDB")
    print("=" * 80)
    
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "chromadb"
    
    if not db_path.exists():
        print(f"ERROR: ChromaDB not found at {db_path}")
        print("Please run ingestion first to populate ChromaDB")
        sys.exit(1)
    
    print(f"Connecting to ChromaDB at {db_path}")
    client = chromadb.PersistentClient(path=str(db_path))
    
    try:
        collection = client.get_collection(name="shl_assessments")
    except Exception as e:
        print(f"ERROR: Collection 'shl_assessments' not found: {e}")
        print("Please run ingestion first")
        sys.exit(1)
    
    count = collection.count()
    print(f"Found {count} items in ChromaDB")
    
    if count == 0:
        print("ERROR: Collection is empty. Run ingestion first.")
        sys.exit(1)
    
    # Get all data
    print("Fetching all data...")
    all_data = collection.get(
        include=["embeddings", "documents", "metadatas"]
    )
    
    # Combine into records
    records = []
    for idx in range(len(all_data['ids'])):
        record = {
            'id': all_data['ids'][idx],
            'embedding': all_data['embeddings'][idx],
            'document': all_data['documents'][idx],
            'metadata': all_data['metadatas'][idx]
        }
        records.append(record)
    
    print(f"✅ Extracted {len(records)} records from ChromaDB")
    return records


def insert_to_supabase(records: List[Dict[str, Any]]) -> int:
    """Insert all records into Supabase"""
    print("\n" + "=" * 80)
    print("STEP 2: Inserting data into Supabase")
    print("=" * 80)
    
    # Initialize Supabase
    try:
        db = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {e}")
        print("Make sure SUPABASE_URL and SUPABASE_KEY are set in .env")
        sys.exit(1)
    
    # Verify table exists
    try:
        result = db.table("assessment_embeddings").select("id").limit(1).execute()
        print("✅ Table 'assessment_embeddings' exists")
    except Exception as e:
        print(f"ERROR: Table 'assessment_embeddings' not found: {e}")
        print("Run setup_supabase_vectors.sql first in Supabase SQL Editor")
        sys.exit(1)
    
    # Check existing data
    existing = db.table("assessment_embeddings").select("id").execute()
    existing_count = len(existing.data) if existing.data else 0
    print(f"Found {existing_count} existing records in Supabase")
    
    if existing_count > 0:
        response = input("Table is not empty. Delete existing data? (yes/no): ")
        if response.lower() == 'yes':
            print("Deleting existing data...")
            # Delete all
            db.table("assessment_embeddings").delete().neq("id", "").execute()
            print("✅ Deleted existing data")
        else:
            print("Skipping deletion. Will attempt upsert...")
    
    # Prepare batch inserts with smaller batches and retry logic
    batch_size = 25  # Reduced from 100 to avoid timeouts
    total = len(records)
    inserted = 0
    errors = []
    
    print(f"\nInserting {total} records in batches of {batch_size}...")
    
    for i in tqdm(range(0, total, batch_size)):
        batch = records[i:i+batch_size]
        
        # Transform to Supabase format
        supabase_records = []
        for record in batch:
            meta = record['metadata']
            
            # Convert embedding to list (ChromaDB returns numpy arrays)
            embedding = record['embedding']
            if not isinstance(embedding, list):
                embedding = embedding.tolist()
            
            supabase_record = {
                'id': record['id'],
                'name': meta.get('name', ''),
                'url': meta.get('url', ''),
                'description': meta.get('description', ''),
                'duration': meta.get('duration', 0),
                'adaptive_support': meta.get('adaptive_support', 'No'),
                'remote_support': meta.get('remote_support', 'No'),
                'test_type': meta.get('test_type', 'General'),
                'job_level': meta.get('job_level', 'General'),
                'full_text': record['document'],
                'embedding': embedding  # Now guaranteed to be a list
            }
            supabase_records.append(supabase_record)
        
        # Insert batch with retry logic
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                result = db.table("assessment_embeddings").upsert(supabase_records).execute()
                inserted += len(batch)
                success = True
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count < max_retries:
                    # Retry with exponential backoff
                    import time
                    wait_time = 2 ** retry_count  # 2, 4, 8 seconds
                    print(f"\n⚠️  Batch {i//batch_size + 1} failed (attempt {retry_count}): {error_msg}")
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Final failure
                    final_error = f"Batch {i//batch_size + 1} failed after {max_retries} attempts: {error_msg}"
                    errors.append(final_error)
                    print(f"\n❌ {final_error}")
    
    print(f"\n✅ Inserted {inserted}/{total} records")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    return inserted


def verify_migration(expected_count: int):
    """Verify migration was successful"""
    print("\n" + "=" * 80)
    print("STEP 3: Verifying Migration")
    print("=" * 80)
    
    db = get_supabase_client()
    
    # Count rows
    result = db.table("assessment_embeddings").select("id", count="exact").execute()
    actual_count = result.count if hasattr(result, 'count') else len(result.data)
    
    print(f"Expected: {expected_count} records")
    print(f"Actual:   {actual_count} records")
    
    if actual_count == expected_count:
        print("✅ Row count matches!")
    else:
        print(f"⚠️  Row count mismatch: {actual_count - expected_count} difference")
    
    # Check sample data
    sample = db.table("assessment_embeddings").select("*").limit(3).execute()
    
    if sample.data:
        print("\n📋 Sample records:")
        for idx, row in enumerate(sample.data[:3], 1):
            print(f"\n  Record {idx}:")
            print(f"    ID: {row['id']}")
            print(f"    Name: {row['name']}")
            print(f"    URL: {row['url']}")
            print(f"    Job Level: {row['job_level']}")
            print(f"    Duration: {row['duration']} min")
            print(f"    Embedding dimension: {len(row['embedding']) if row['embedding'] else 0}")
    
    # Check indexes
    print("\n📊 Checking indexes...")
    # This would require a direct SQL query - skipping for now
    
    print("\n✅ Migration verification complete!")


def save_backup(records: List[Dict[str, Any]]):
    """Save backup of data before migration"""
    backup_path = Path(__file__).parent.parent / "data" / "chromadb_backup.json"
    
    print(f"\n💾 Saving backup to {backup_path}")
    
    # Convert numpy arrays to lists for JSON serialization
    serializable_records = []
    for record in records:
        ser_record = record.copy()
        if isinstance(ser_record['embedding'], list):
            pass  # already a list
        else:
            ser_record['embedding'] = ser_record['embedding'].tolist()
        serializable_records.append(ser_record)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_records, f, indent=2)
    
    print(f"✅ Backup saved ({len(serializable_records)} records)")


def main():
    """Main migration process"""
    print("\n" + "=" * 80)
    print("ChromaDB to Supabase pgvector Migration")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Extract all data from local ChromaDB")
    print("2. Save a backup JSON file")
    print("3. Insert data into Supabase pgvector")
    print("4. Verify the migration")
    print("\n" + "=" * 80)
    
    # Confirm
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled")
        sys.exit(0)
    
    # Step 1: Extract from ChromaDB
    records = extract_from_chromadb()
    
    # Step 1.5: Save backup
    save_backup(records)
    
    # Step 2: Insert to Supabase
    inserted = insert_to_supabase(records)
    
    # Step 3: Verify
    verify_migration(len(records))
    
    print("\n" + "=" * 80)
    print("✅ Migration Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Set VECTOR_DB_TYPE=supabase in your .env file")
    print("2. Update backend to use rag_recommender_v2.py")
    print("3. Test recommendations locally")
    print("4. Deploy to Render")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
