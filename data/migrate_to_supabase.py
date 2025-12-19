"""
Supabase Migration Script
Migrates scraped assessment data to Supabase with proper schema
Generates embeddings using HuggingFace API
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from supabase import create_client, Client

# Import embedding service - with fallback for standalone execution
try:
    from app.services.embedding_service import get_embedding_service
except ImportError:
    # Standalone execution - define embedding service here
    from huggingface_hub import InferenceClient
    import numpy as np
    
    class HuggingFaceEmbeddingService:
        def __init__(self):
            self.api_key = os.getenv('HUGGINGFACE_API_KEY')
            if not self.api_key:
                raise ValueError("HUGGINGFACE_API_KEY environment variable is required")
            
            self.use_space = os.getenv('USE_HUGGINGFACE_SPACE', 'false').lower() == 'true'
            self.space_url = os.getenv('HUGGINGFACE_SPACE_URL')
            self.model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            
            if self.use_space and self.space_url:
                print(f"✅ Using HuggingFace Space: {self.space_url}")
            else:
                self.client = InferenceClient(token=self.api_key)
                print(f"✅ HuggingFace embedding service initialized (model: {self.model_name})")
        
        def encode(self, texts: List[str], **kwargs) -> np.ndarray:
            # Use Space if configured
            if self.use_space and self.space_url:
                return self._encode_via_space(texts)
            else:
                return self._encode_via_inference_api(texts)
        
        def _encode_via_space(self, texts: List[str]) -> np.ndarray:
            """Encode using custom HuggingFace Space"""
            import requests
            
            all_embeddings = []
            max_retries = 3
            batch_size = 32  # Space can handle larger batches
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f"{self.space_url}/embed",
                            json={"texts": batch, "normalize": True},
                            timeout=30
                        )
                        response.raise_for_status()
                        
                        data = response.json()
                        batch_embeddings = data.get("embeddings", [])
                        all_embeddings.extend(batch_embeddings)
                        break  # Success
                        
                    except Exception as e:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            print(f"  ⏳ Space request failed, retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            print(f"  ❌ Failed to get embeddings from Space: {e}")
                            raise
            
            return np.array(all_embeddings, dtype=np.float32)
        
        def _encode_via_inference_api(self, texts: List[str]) -> np.ndarray:
            """Encode using HuggingFace Inference API"""
            all_embeddings = []
            max_retries = 3
            
            for text in texts:
                for attempt in range(max_retries):
                    try:
                        embedding = self.client.feature_extraction(
                            text=text, 
                            model=self.model_name,
                            timeout=60.0  # Increased timeout to 60 seconds
                        )
                        if isinstance(embedding, list) and len(embedding) > 0:
                            if isinstance(embedding[0], list):
                                all_embeddings.append(embedding[0])
                            else:
                                all_embeddings.append(embedding)
                        else:
                            all_embeddings.append(embedding)
                        
                        time.sleep(1.0)  # Rate limiting - increased to 1s
                        break  # Success
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        
                        if "timeout" in error_msg or "504" in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                                print(f"  ⏳ Timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"  ❌ Failed after {max_retries} timeout attempts")
                                raise
                        elif "rate limit" in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 3
                                print(f"  ⏳ Rate limited, waiting {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                raise
                        else:
                            print(f"  ❌ Error generating embedding: {e}")
                            raise
            
            return np.array(all_embeddings, dtype=np.float32)


    
    def get_embedding_service():
        return HuggingFaceEmbeddingService()



class SupabaseMigration:
    """
    Handles migration of assessment data to Supabase
    """
    
    def __init__(self):
        """Initialize Supabase client and embedding service"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.embedding_service = None
        
        print("✅ Supabase client initialized")
    
    def _ensure_embedding_service(self):
        """Lazy load embedding service"""
        if self.embedding_service is None:
            print("🔄 Initializing HuggingFace embedding service...")
            self.embedding_service = get_embedding_service()
            print("✅ Embedding service ready")
    
    def load_data(self, filepath: str) -> Dict[str, Any]:
        """Load assessment data from JSON file"""
        print(f"📂 Loading data from {filepath}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assessments = data.get('assessments', [])
        print(f"✅ Loaded {len(assessments)} assessments")
        
        return data
    
    def _create_embedding_text(self, assessment: Dict) -> str:
        """Create text representation for embedding"""
        parts = [
            f"Assessment: {assessment.get('name', '')}",
            f"Type: {assessment.get('type', '')}",
        ]
        
        if assessment.get('job_family'):
            parts.append(f"Job Family: {assessment['job_family']}")
        
        if assessment.get('job_level'):
            parts.append(f"Job Level: {assessment['job_level']}")
        
        if assessment.get('description'):
            parts.append(f"Description: {assessment['description']}")
        
        if assessment.get('skills'):
            parts.append(f"Skills: {', '.join(assessment['skills'])}")
        
        if assessment.get('industries'):
            parts.append(f"Industries: {', '.join(assessment['industries'])}")
        
        return " | ".join(parts)
    
    def migrate_assessments(self, assessments: List[Dict], batch_size: int = 10):
        """
        Migrate assessments to Supabase
        
        Args:
            assessments: List of assessment dictionaries
            batch_size: Number of assessments to process in one batch
        """
        self._ensure_embedding_service()
        
        print(f"\n🚀 Starting migration of {len(assessments)} assessments...")
        print(f"📦 Batch size: {batch_size}")
        
        total_migrated = 0
        total_skipped = 0
        total_errors = 0
        
        for i in range(0, len(assessments), batch_size):
            batch = assessments[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(assessments) + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} assessments)...")
            
            for assessment in batch:
                try:
                    # Check if assessment already exists
                    existing = self.client.table('assessments').select('id').eq('id', assessment['id']).execute()
                    
                    if existing.data:
                        print(f"  ⏭️  Skipping {assessment['id']} (already exists)")
                        total_skipped += 1
                        continue
                    
                    # Generate embedding
                    embedding_text = self._create_embedding_text(assessment)
                    embedding = self.embedding_service.encode([embedding_text])[0]
                    embedding_list = embedding.tolist()
                    
                    # Prepare assessment data for main table
                    assessment_data = {
                        'id': assessment['id'],
                        'name': assessment['name'],
                        'type': assessment['type'],
                        'remote_testing': assessment.get('remote_testing', False),
                        'adaptive': assessment.get('adaptive', False),
                        'job_family': assessment.get('job_family'),
                        'job_level': assessment.get('job_level'),
                        'description': assessment.get('description', ''),
                        'duration': assessment.get('duration'),
                        'embedding': embedding_list
                    }
                    
                    # Insert into assessments table
                    result = self.client.table('assessments').insert(assessment_data).execute()
                    
                    if not result.data:
                        raise Exception("Failed to insert assessment")
                    
                    # Insert related data
                    self._insert_related_data(assessment)
                    
                    print(f"  ✅ Migrated: {assessment['name']}")
                    total_migrated += 1
                    
                    # Rate limiting for HuggingFace API
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ❌ Error migrating {assessment.get('id', 'unknown')}: {e}")
                    total_errors += 1
                    continue
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"✅ Successfully migrated: {total_migrated}")
        print(f"⏭️  Skipped (already exist): {total_skipped}")
        print(f"❌ Errors: {total_errors}")
        print(f"📊 Total processed: {total_migrated + total_skipped + total_errors}")
        print("="*60)
    
    def _insert_related_data(self, assessment: Dict):
        """Insert related data (test_types, industries, languages, skills)"""
        assessment_id = assessment['id']
        
        # Insert test_types
        if assessment.get('test_types'):
            for test_type in assessment['test_types']:
                try:
                    self.client.table('test_types').insert({
                        'assessment_id': assessment_id,
                        'test_type': test_type
                    }).execute()
                except Exception as e:
                    # Ignore duplicate errors
                    if 'duplicate' not in str(e).lower():
                        print(f"    ⚠️  Error inserting test_type: {e}")
        
        # Insert industries
        if assessment.get('industries'):
            for industry in assessment['industries']:
                try:
                    self.client.table('industries').insert({
                        'assessment_id': assessment_id,
                        'industry': industry
                    }).execute()
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"    ⚠️  Error inserting industry: {e}")
        
        # Insert languages
        if assessment.get('languages'):
            for language in assessment['languages']:
                try:
                    self.client.table('languages').insert({
                        'assessment_id': assessment_id,
                        'language': language
                    }).execute()
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"    ⚠️  Error inserting language: {e}")
        
        # Insert skills
        if assessment.get('skills'):
            for skill in assessment['skills']:
                try:
                    self.client.table('skills').insert({
                        'assessment_id': assessment_id,
                        'skill': skill
                    }).execute()
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"    ⚠️  Error inserting skill: {e}")
    
    def verify_migration(self):
        """Verify migration was successful"""
        print("\n🔍 Verifying migration...")
        
        # Count assessments
        assessments = self.client.table('assessments').select('id', count='exact').execute()
        assessment_count = len(assessments.data) if assessments.data else 0
        
        # Count related data
        test_types = self.client.table('test_types').select('id', count='exact').execute()
        industries = self.client.table('industries').select('id', count='exact').execute()
        languages = self.client.table('languages').select('id', count='exact').execute()
        skills = self.client.table('skills').select('id', count='exact').execute()
        
        print("\n📊 Database Statistics:")
        print(f"  Assessments: {assessment_count}")
        print(f"  Test Types: {len(test_types.data) if test_types.data else 0}")
        print(f"  Industries: {len(industries.data) if industries.data else 0}")
        print(f"  Languages: {len(languages.data) if languages.data else 0}")
        print(f"  Skills: {len(skills.data) if skills.data else 0}")
        
        # Sample query using the view
        print("\n🔍 Testing assessment_details view...")
        sample = self.client.table('assessment_details').select('*').limit(1).execute()
        
        if sample.data:
            print("✅ View is working correctly")
            print(f"   Sample: {sample.data[0].get('name', 'N/A')}")
        else:
            print("⚠️  No data in view")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate assessment data to Supabase')
    parser.add_argument('--file', default='data/shl_products_complete.json',
                       help='Path to JSON file with assessment data')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Number of assessments to process in one batch')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify existing data, do not migrate')
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create migrator
    migrator = SupabaseMigration()
    
    if args.verify_only:
        migrator.verify_migration()
    else:
        # Load and migrate data
        data = migrator.load_data(args.file)
        assessments = data.get('assessments', [])
        
        if not assessments:
            print("❌ No assessments found in file")
            return
        
        # Migrate
        migrator.migrate_assessments(assessments, batch_size=args.batch_size)
        
        # Verify
        migrator.verify_migration()
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
