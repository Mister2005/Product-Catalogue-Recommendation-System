"""
Debug test of Supabase vector search directly
"""
import sys
import os
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from root directory (parent of backend)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

print("Testing Supabase Vector Search Directly...")
print(f"VECTOR_DB_TYPE = {os.getenv('VECTOR_DB_TYPE', 'not set')}\n")

from app.core.vector_db import get_vector_db
from app.services.embedding_service import HuggingFaceEmbeddingService

# Initialize
embed_service = HuggingFaceEmbeddingService()
vector_db = get_vector_db()

print(f"Vector DB count: {vector_db.count()}")

# Test query
query = "Python developer internship"
print(f"\nQuery: '{query}'")

# Get embedding
print("Generating embedding...")
embedding = embed_service.encode(query, is_query=True).tolist()
print(f"Embedding dimension: {len(embedding)}")

# Search
print("\nSearching...")
metadatas, documents = vector_db.search(embedding, n_results=5)

print(f"\n✅ Got {len(metadatas)} results:")
for i, (meta, doc) in enumerate(zip(metadatas, documents), 1):
    print(f"{i}. {meta['name']} ({meta.get('job_level', 'N/A')})")
    print(f"   URL: {meta['url']}")
    print(f"   Doc preview: {doc[:100]}...")
    print()
