"""
Populate assessment_urls table in Supabase
Combines data from Excel, web scraping, and URL generation
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from app.core.database import get_supabase_client
from app.core.logging import log
from shl_url_scraper import SHLURLScraper, generate_url_from_name
from typing import Dict, List
import time


def load_urls_from_excel() -> Dict[str, str]:
    """
    Load known URLs from Gen_AI Dataset.xlsx
    
    Returns:
        Dict mapping assessment name to URL
    """
    log.info("Loading URLs from Excel file...")
    
    try:
        dataset_path = Path(__file__).parent.parent / "Gen_AI Dataset.xlsx"
        
        if not dataset_path.exists():
            log.warning(f"Excel file not found at {dataset_path}")
            return {}
        
        df = pd.read_excel(dataset_path, sheet_name='Train-Set')
        
        # Extract unique assessment URLs
        url_map = {}
        for url in df['Assessment_url'].unique():
            # Extract name from URL or use a placeholder
            # We'll match these to actual assessments later
            if '/view/' in url:
                slug = url.split('/view/')[-1].rstrip('/')
                url_map[slug] = url
        
        log.info(f"Loaded {len(url_map)} URLs from Excel")
        return url_map
        
    except Exception as e:
        log.error(f"Error loading Excel file: {e}")
        return {}


def match_url_to_assessment(assessment_name: str, url_map: Dict[str, str], scraped_urls: List[Dict]) -> tuple[str, str, str]:
    """
    Match an assessment to its URL using multiple strategies
    
    Args:
        assessment_name: Name of the assessment
        url_map: Dict of slug -> URL from Excel
        scraped_urls: List of scraped assessment dicts
        
    Returns:
        Tuple of (url, slug, source)
    """
    # Strategy 1: Try to find in scraped URLs by exact name match
    for scraped in scraped_urls:
        if scraped['name'].lower() == assessment_name.lower():
            return scraped['url'], scraped['slug'], 'scraped'
    
    # Strategy 2: Try to find in scraped URLs by fuzzy name match
    assessment_lower = assessment_name.lower()
    for scraped in scraped_urls:
        scraped_lower = scraped['name'].lower()
        # Check if names are similar (contains or partial match)
        if assessment_lower in scraped_lower or scraped_lower in assessment_lower:
            return scraped['url'], scraped['slug'], 'scraped'
    
    # Strategy 3: Generate slug and check if it's in Excel data
    generated_url, slug = generate_url_from_name(assessment_name)
    
    if slug in url_map:
        return url_map[slug], slug, 'excel'
    
    # Try with "-new" suffix
    if f"{slug}-new" in url_map:
        return url_map[f"{slug}-new"], f"{slug}-new", 'excel'
    
    # Strategy 4: Generate URL as fallback
    return generated_url, slug, 'generated'


def populate_url_mappings():
    """Main function to populate assessment_urls table"""
    log.info("=" * 60)
    log.info("Starting URL mapping population")
    log.info("=" * 60)
    
    # Initialize Supabase client
    db = get_supabase_client()
    
    # Step 1: Load all assessments from database
    log.info("\n[1/5] Loading assessments from Supabase...")
    response = db.table("assessments").select("id, name, type").execute()
    assessments = response.data
    log.info(f"Found {len(assessments)} assessments in database")
    
    # Step 2: Load URLs from Excel
    log.info("\n[2/5] Loading known URLs from Excel...")
    excel_url_map = load_urls_from_excel()
    
    # Step 3: Scrape URLs from SHL website
    log.info("\n[3/5] Scraping URLs from SHL website...")
    log.info("NOTE: This may take a few minutes and might not work if SHL blocks scraping")
    
    try:
        scraper = SHLURLScraper(delay=2.0)  # 2 second delay between requests
        scraped_urls = scraper.scrape_all_assessments()
        log.info(f"Successfully scraped {len(scraped_urls)} URLs")
    except Exception as e:
        log.warning(f"Scraping failed: {e}")
        log.info("Continuing with Excel data and URL generation...")
        scraped_urls = []
    
    # Step 4: Match assessments to URLs
    log.info("\n[4/5] Matching assessments to URLs...")
    url_mappings = []
    
    for assessment in assessments:
        url, slug, source = match_url_to_assessment(
            assessment['name'],
            excel_url_map,
            scraped_urls
        )
        
        url_mappings.append({
            'id': assessment['id'],
            'assessment_name': assessment['name'],
            'url': url,
            'url_slug': slug,
            'source': source,
            'verified': source in ['excel', 'scraped']  # Excel and scraped URLs are more reliable
        })
    
    # Print statistics
    sources = {}
    for mapping in url_mappings:
        source = mapping['source']
        sources[source] = sources.get(source, 0) + 1
    
    log.info(f"\nURL Source Statistics:")
    log.info(f"  - Excel (verified): {sources.get('excel', 0)}")
    log.info(f"  - Scraped: {sources.get('scraped', 0)}")
    log.info(f"  - Generated: {sources.get('generated', 0)}")
    log.info(f"  - Total: {len(url_mappings)}")
    
    # Step 5: Insert into Supabase
    log.info("\n[5/5] Inserting URL mappings into Supabase...")
    
    try:
        # Delete existing mappings
        log.info("Clearing existing URL mappings...")
        db.table("assessment_urls").delete().neq('id', '').execute()
        
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(url_mappings), batch_size):
            batch = url_mappings[i:i+batch_size]
            db.table("assessment_urls").insert(batch).execute()
            log.info(f"Inserted batch {i//batch_size + 1}/{(len(url_mappings)-1)//batch_size + 1}")
            time.sleep(0.5)  # Small delay between batches
        
        log.info(f"\n✅ Successfully populated {len(url_mappings)} URL mappings!")
        
        # Verify insertion
        count_response = db.table("assessment_urls").select("id", count="exact").execute()
        log.info(f"Verification: {count_response.count} rows in assessment_urls table")
        
    except Exception as e:
        log.error(f"Error inserting into Supabase: {e}")
        raise
    
    log.info("\n" + "=" * 60)
    log.info("URL mapping population complete!")
    log.info("=" * 60)


if __name__ == "__main__":
    populate_url_mappings()
