"""
Regenerate embeddings with assessment names weighted 3x for better exact matching
This will help the system find assessments by their specific names
"""
import sys
from pathlib import Path
sys.path.insert(0, 'backend')

from app.core.database import get_supabase_client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import time
from tqdm import tqdm

load_dotenv(Path('.env'))
db = get_supabase_client()

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

print("="*80)
print(f"REGENERATING EMBEDDINGS WITH WEIGHTED ASSESSMENT NAMES")
print(f"Model: {EMBEDDING_MODEL} (384 dimensions)")
print("="*80)

# Fetch all assessments
print("\nFetching all 377 assessments...")
result = db.table('assessment_embeddings').select(
    'id', 'name', 'description', 'test_type', 'job_level', 'duration', 'remote_support'
).execute()
assessments = result.data
print(f"Loaded {len(assessments)} records")

# Load model
print(f"\nLoading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("✅ Model loaded")

# Generate embeddings with weighted names
batch_size = 16
total = len(assessments)

print(f"\nGenerating embeddings with 3x weighted names (batches of {batch_size})...")

updated_count = 0
error_count = 0

for i in tqdm(range(0, total, batch_size), desc="Processing"):
    batch = assessments[i:i+batch_size]
    
    # Build text with TRIPLED assessment names for stronger matching
    texts = []
    for item in batch:
        # TRIPLE the name to increase its weight in embeddings
        name = item['name']
        parts = [name, name, name]  # Name appears 3 times
        
        desc = item.get('description', '')
        if desc and desc != f"Assessment for {name}":
            parts.append(desc[:150])
        
        if item.get('test_type') and item['test_type'] != 'General':
            parts.append(f"Type: {item['test_type']}")
        
        if item.get('job_level') and item['job_level'] != 'General':
            parts.append(f"Level: {item['job_level']}")
        
        if item.get('duration', 0) > 0:
            parts.append(f"{item['duration']}min")
        
        texts.append('. '.join(parts))
    
    # Generate embeddings
    try:
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        
        # Update database
        for idx, item in enumerate(batch):
            try:
                db.table('assessment_embeddings').update({
                    'embedding': vectors[idx].tolist(),
                    'full_text': texts[idx],
                    'updated_at': time.strftime('%Y-%m-%dT%H:%M:%S')
                }).eq('id', item['id']).execute()
                updated_count += 1
            except Exception as e:
                error_count += 1
        
    except Exception as e:
        print(f"\n❌ Error in batch {i//batch_size + 1}: {e}")
        error_count += len(batch)

print(f"\n{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print(f"Updated: {updated_count}/{total}")
print(f"Errors: {error_count}")

# Verification
null_check = db.table('assessment_embeddings').select('id').is_('embedding', 'null').execute()
print(f"\nRecords with NULL embedding: {len(null_check.data)}")

if updated_count == 377 and len(null_check.data) == 0:
    print("\n✅ SUCCESS: All 377 assessments have weighted embeddings!")
else:
    print(f"\n⚠️ Check: {updated_count} updated, {len(null_check.data)} null")

print("\n✅ Weighted embedding generation complete!")
