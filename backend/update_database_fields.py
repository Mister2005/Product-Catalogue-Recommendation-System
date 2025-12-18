"""
Script to check and update Supabase assessments table with missing fields
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

def check_database_schema():
    """Check what fields exist in the database"""
    print("🔍 Checking database schema...")
    try:
        # Fetch one assessment to see what fields exist
        response = supabase.table("assessments").select("*").limit(1).execute()
        if response.data:
            fields = response.data[0].keys()
            print(f"✅ Database has {len(fields)} fields:")
            for field in sorted(fields):
                print(f"   - {field}")
            
            # Check for critical fields
            critical_fields = ['job_family', 'job_level', 'duration', 'languages']
            missing = [f for f in critical_fields if f not in fields]
            if missing:
                print(f"\n⚠️  Missing critical fields: {', '.join(missing)}")
            else:
                print(f"\n✅ All critical fields present!")
        else:
            print("❌ No assessments found in database")
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

def update_missing_fields():
    """Update assessments with missing job_family, job_level, etc."""
    print("\n🔄 Updating assessments with missing fields...")
    
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
    
    # Get current database assessments
    response = supabase.table("assessments").select("id, name, job_family, job_level, duration").execute()
    db_assessments = {a['id']: a for a in response.data}
    print(f"💾 Found {len(db_assessments)} assessments in database")
    
    # Update each assessment
    updated = 0
    for assessment in all_assessments:
        assessment_id = assessment['id']
        
        if assessment_id not in db_assessments:
            print(f"⚠️  Assessment {assessment_id} not in database, skipping")
            continue
        
        db_assessment = db_assessments[assessment_id]
        
        # Check if needs update
        needs_update = False
        update_data = {}
        
        if not db_assessment.get('job_family') and assessment.get('job_family'):
            update_data['job_family'] = assessment['job_family']
            needs_update = True
        
        if not db_assessment.get('job_level') and assessment.get('job_level'):
            update_data['job_level'] = assessment['job_level']
            needs_update = True
        
        if not db_assessment.get('duration') and assessment.get('duration'):
            update_data['duration'] = assessment['duration']
            needs_update = True
        
        if needs_update:
            try:
                supabase.table("assessments").update(update_data).eq("id", assessment_id).execute()
                updated += 1
                print(f"✅ Updated {db_assessment['name']}: {update_data}")
            except Exception as e:
                print(f"❌ Failed to update {assessment_id}: {e}")
    
    print(f"\n✨ Updated {updated} assessments")

if __name__ == "__main__":
    print("=" * 60)
    print("SHL Assessment Database Field Updater")
    print("=" * 60)
    
    check_database_schema()
    
    print("\n" + "=" * 60)
    response = input("\nDo you want to update missing fields? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        update_missing_fields()
        print("\n🎉 Done!")
    else:
        print("\n❌ Cancelled")
