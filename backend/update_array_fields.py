"""
Update Supabase assessments with missing array fields (skills, test_types, industries, languages)
"""
import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def update_assessments_with_array_fields():
    """Update assessments with skills, test_types, industries, and languages"""
    print("🔄 Updating assessments with array fields...")
    
    # Load JSON data
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shl_products.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Flatten all assessments
    all_assessments = []
    for category in ['pre_packaged_solutions', 'individual_test_solutions', 
                     'skill_specific_assessments', 'industry_solutions']:
        if category in data:
            all_assessments.extend(data[category])
    
    print(f"📦 Loaded {len(all_assessments)} assessments from JSON")
    
    # Update each assessment
    updated = 0
    failed = 0
    
    for assessment in all_assessments:
        assessment_id = assessment['id']
        
        try:
            # Prepare update data with all array fields
            update_data = {
                'skills': assessment.get('skills', []),
                'test_types': assessment.get('test_types', []),
                'industries': assessment.get('industries', []),
                'languages': assessment.get('languages', ['English']),
                'job_family': assessment.get('job_family'),
                'job_level': assessment.get('job_level'),
                'duration': assessment.get('duration')
            }
            
            # Update in Supabase
            result = supabase.table("assessments").update(update_data).eq("id", assessment_id).execute()
            
            if result.data:
                updated += 1
                print(f"✅ Updated {assessment['name']}")
                print(f"   Skills: {len(update_data['skills'])}, Test Types: {len(update_data['test_types'])}")
            else:
                print(f"⚠️  No data returned for {assessment_id}")
                
        except Exception as e:
            failed += 1
            print(f"❌ Failed to update {assessment_id}: {e}")
    
    print(f"\n✨ Updated {updated} assessments")
    print(f"❌ Failed {failed} assessments")

if __name__ == "__main__":
    print("=" * 60)
    print("SHL Assessment Array Fields Updater")
    print("=" * 60)
    
    response = input("\nThis will update all assessments with skills, test_types, industries, and languages.\nContinue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        update_assessments_with_array_fields()
        print("\n🎉 Done!")
    else:
        print("\n❌ Cancelled")
