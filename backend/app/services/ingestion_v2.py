"""
Unified Ingestion Script for Both ChromaDB and Supabase
Supports switching backends via VECTOR_DB_TYPE environment variable
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
COLLECTION_NAME = "shl_assessments"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chromadb").lower()

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # backend/
DATA_FILE_PATH = BASE_DIR / "backend" / "data" / "shl_products_complete.json"

# Adjust if running inside container structure where backend might be CWD
if not DATA_FILE_PATH.exists():
    # Try alternate path if CWD is backend/
    DATA_FILE_PATH = Path("data/shl_products_complete.json")


def clean_duration(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        # Try to parse "11 minutes" etc.
        import re
        match = re.search(r"(\d+)", val)
        if match:
            return int(match.group(1))
    return 0


def load_and_filter_data() -> List[Dict[str, Any]]:
    """Load and filter assessment data"""
    print(f"Loading data from {DATA_FILE_PATH}")
    if not DATA_FILE_PATH.exists():
        print(f"ERROR: File not found at {DATA_FILE_PATH}")
        sys.exit(1)

    with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
        content = json.load(f)
        
    # Content is {"metadata": ..., "assessments": [...]}
    data_list = content.get("assessments", [])
    print(f"Loaded {len(data_list)} raw assessments.")
    
    valid_data = []
    
    for item in data_list:
        # Filter logic
        # Requirement: Filter out "Pre-packaged Job Solutions"
        # The file has a "type" field
        atype = item.get("type", "")
        if "Pre-packaged" in atype or "Job Solution" in atype:
            if atype != "Individual Test Solution":  # Keep Individual Test Solutions
                continue
                
        # Also check name/categorization if type is ambiguous
        if item.get("job_family") == "Pre-packaged Job Solutions":
             continue

        # Extract Fields
        name = item.get("name", "")
        
        # INFER JOB LEVEL
        name_lower = name.lower()
        job_level = "General"
        if any(x in name_lower for x in ["graduate", "entry", "intern", "junior", "apprentice"]):
            job_level = "Entry_Level"
        elif any(x in name_lower for x in ["manager", "senior", "lead", "head", "director", "executive", "vp"]):
            job_level = "Manager_Senior"
            
        description = item.get("description", "")
        url_id = item.get('id', '').replace('_', '-')
        url = f"https://www.shl.com/solutions/products/product-catalog/view/{url_id}/"  # Reconstruct URL if missing
        
        duration = clean_duration(item.get("duration"))
        adaptive = "Yes" if item.get("adaptive") else "No"
        remote = "Yes" if item.get("remote_testing") else "No"
        
        test_types = item.get("test_types", [])
        test_type_str = test_types[0] if test_types else "General"
        
        # Create full text for embedding
        # Title + Description + Keywords
        full_text = f"{name}. {description}. {test_type_str}"
        
        record = {
            "name": name,
            "url": url,
            "description": description,
            "duration": duration,
            "adaptive_support": adaptive,
            "remote_support": remote,
            "test_type": test_type_str, 
            "full_text": full_text,
            "job_level": job_level
        }
        valid_data.append(record)
        
    print(f"Filtered down to {len(valid_data)} valid assessments (Individual Test Solutions).")
    return valid_data


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using sentence-transformers"""
    from sentence_transformers import SentenceTransformer
    
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print("Generating embeddings...")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    
    return embeddings.tolist()


def ingest_to_chromadb(data: List[Dict[str, Any]]):
    """Ingest data to ChromaDB"""
    import chromadb
    
    print("\n" + "=" * 80)
    print("Ingesting to ChromaDB")
    print("=" * 80)
    
    CHROMA_DB_DIR = "backend/data/chromadb"
    db_path = BASE_DIR / CHROMA_DB_DIR
    os.makedirs(db_path, exist_ok=True)
    
    print(f"Initializing ChromaDB in {db_path}")
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Reset collection
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Deleted existing collection")
    except:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Generate embeddings
    texts = [item["full_text"] for item in data]
    embeddings = generate_embeddings(texts)
    
    # Insert in batches
    batch_size = 32
    total = len(data)
    
    print("Inserting into ChromaDB...")
    for i in tqdm(range(0, total, batch_size)):
        batch = data[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        
        documents = [item["full_text"] for item in batch]
        ids = [str(i + idx) for idx, _ in enumerate(batch)]
        metadatas = [{
            "name": item["name"],
            "url": item["url"],
            "duration": item["duration"],
            "adaptive_support": item["adaptive_support"],
            "remote_support": item["remote_support"],
            "test_type": item["test_type"],
            "job_level": item["job_level"],
            "description": item["description"][:1000]
        } for item in batch]
        
        collection.add(
            ids=ids,
            embeddings=batch_embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
    print(f"✅ Successfully indexed {total} items into ChromaDB.")


def ingest_to_supabase(data: List[Dict[str, Any]]):
    """Ingest data to Supabase"""
    sys.path.append(str(BASE_DIR / "backend"))
    from app.core.database import get_supabase_client
    
    print("\n" + "=" * 80)
    print("Ingesting to Supabase pgvector")
    print("=" * 80)
    
    # Initialize Supabase
    try:
        db = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Verify table exists
    try:
        result = db.table("assessment_embeddings").select("id").limit(1).execute()
        print("✅ Table 'assessment_embeddings' exists")
    except Exception as e:
        print(f"ERROR: Table 'assessment_embeddings' not found: {e}")
        print("Run setup_supabase_vectors.sql first in Supabase SQL Editor")
        sys.exit(1)
    
    # Clear existing data
    response = input("Delete existing data in Supabase? (yes/no): ")
    if response.lower() == 'yes':
        print("Deleting existing data...")
        db.table("assessment_embeddings").delete().neq("id", "").execute()
        print("✅ Deleted existing data")
    
    # Generate embeddings
    texts = [item["full_text"] for item in data]
    embeddings = generate_embeddings(texts)
    
    # Insert in batches
    batch_size = 100
    total = len(data)
    inserted = 0
    
    print("Inserting into Supabase...")
    for i in tqdm(range(0, total, batch_size)):
        batch = data[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        
        # Prepare Supabase records
        supabase_records = []
        for idx, item in enumerate(batch):
            record = {
                'id': str(i + idx),
                'name': item['name'],
                'url': item['url'],
                'description': item['description'],
                'duration': item['duration'],
                'adaptive_support': item['adaptive_support'],
                'remote_support': item['remote_support'],
                'test_type': item['test_type'],
                'job_level': item['job_level'],
                'full_text': item['full_text'],
                'embedding': batch_embeddings[idx]
            }
            supabase_records.append(record)
        
        # Insert batch
        try:
            result = db.table("assessment_embeddings").upsert(supabase_records).execute()
            inserted += len(batch)
        except Exception as e:
            print(f"\n❌ Batch {i//batch_size + 1} failed: {e}")
    
    print(f"✅ Successfully indexed {inserted}/{total} items into Supabase.")


def ingest():
    """Main ingestion function"""
    print("\n" + "=" * 80)
    print(f"SHL Assessment Ingestion - {VECTOR_DB_TYPE.upper()} Backend")
    print("=" * 80)
    
    # Load and filter data
    data = load_and_filter_data()
    
    # Ingest to appropriate backend
    if VECTOR_DB_TYPE == "supabase":
        ingest_to_supabase(data)
    else:
        ingest_to_chromadb(data)
    
    print("\n" + "=" * 80)
    print("✅ Ingestion Complete!")
    print("=" * 80)


if __name__ == "__main__":
    ingest()
