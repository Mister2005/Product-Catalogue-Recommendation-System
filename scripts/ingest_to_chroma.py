import json
import os
import chromadb
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configuration
CHROMA_DB_DIR = "backend/data/chromadb"
COLLECTION_NAME = "shl_assessments"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Paths
BASE_DIR = Path(__file__).parent.parent # Root
DATA_FILE_PATH = BASE_DIR / "data" / "shl_products_complete.json"

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

def ingest():
    print(f"Loading data from {DATA_FILE_PATH}")
    if not DATA_FILE_PATH.exists():
        print(f"ERROR: File not found at {DATA_FILE_PATH}")
        return

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
            if atype != "Individual Test Solution": # Keep Individual Test Solutions
                continue
                
        # Also check name/categorization if type is ambiguous
        if item.get("job_family") == "Pre-packaged Job Solutions":
             continue

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
        url = f"https://www.shl.com/solutions/products/product-catalog/view/{url_id}/" # Reconstruct URL if missing
        
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

    print(f"Initializing ChromaDB in {CHROMA_DB_DIR}")
    db_path = BASE_DIR / CHROMA_DB_DIR
    os.makedirs(db_path, exist_ok=True)
    
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
    
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    batch_size = 32
    total = len(valid_data)
    
    print("Generating embeddings and indexing...")
    for i in tqdm(range(0, total, batch_size)):
        batch = valid_data[i:i+batch_size]
        
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
        
        embeddings = model.encode(documents, normalize_embeddings=True).tolist()
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
    print(f"Successfully indexed {total} items into ChromaDB.")

if __name__ == "__main__":
    ingest()
