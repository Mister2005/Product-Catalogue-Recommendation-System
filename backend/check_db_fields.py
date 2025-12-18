"""
Quick script to see what fields are actually in a database assessment
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Get one assessment and print all its fields
response = supabase.table("assessments").select("*").eq("id", "python_programming").execute()

if response.data:
    assessment = response.data[0]
    print("Assessment fields:")
    print(json.dumps(assessment, indent=2, default=str))
else:
    # Try any assessment
    response = supabase.table("assessments").select("*").limit(1).execute()
    if response.data:
        assessment = response.data[0]
        print("Sample assessment fields:")
        print(json.dumps(assessment, indent=2, default=str))
