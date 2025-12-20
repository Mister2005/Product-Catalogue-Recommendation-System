"""
URL mapping utility for SHL assessments
Maps assessment names to their correct SHL catalog URLs
Now uses Supabase database instead of Excel file
"""
from pathlib import Path
from typing import Dict, Optional
from app.core.logging import log
import re


class AssessmentURLMapper:
    """Maps assessment names to their SHL catalog URLs using Supabase"""
    
    def __init__(self):
        self._url_map: Dict[str, str] = {}  # slug -> URL mapping
        self._name_to_url: Dict[str, str] = {}  # name -> URL mapping
        self._load_url_mapping()
    
    def _load_url_mapping(self):
        """Load URL mapping from Supabase database"""
        try:
            from app.core.database import get_supabase_client
            
            log.info("Loading assessment URLs from Supabase...")
            db = get_supabase_client()
            
            # Fetch all URL mappings from database
            response = db.table("assessment_urls").select("*").execute()
            
            if not response.data:
                log.warning("No URL mappings found in database. Run populate_url_mappings.py first.")
                return
            
            # Build mappings
            for row in response.data:
                slug = row.get('url_slug')
                url = row.get('url')
                name = row.get('assessment_name')
                
                if slug and url:
                    self._url_map[slug] = url
                
                if name and url:
                    # Store both original and lowercase name for fuzzy matching
                    self._name_to_url[name.lower()] = url
            
            log.info(f"Loaded {len(self._url_map)} assessment URL mappings from Supabase")
            
        except Exception as e:
            log.error(f"Failed to load URL mapping from Supabase: {e}")
            log.info("Falling back to URL generation")
    
    def get_url_from_name(self, assessment_name: str) -> str:
        """
        Get URL for an assessment by its name
        
        Args:
            assessment_name: Name of the assessment
            
        Returns:
            Full URL to the assessment
        """
        # Strategy 1: Try exact name match (case-insensitive)
        name_lower = assessment_name.lower()
        if name_lower in self._name_to_url:
            return self._name_to_url[name_lower]
        
        # Strategy 2: Try fuzzy name match
        for db_name, url in self._name_to_url.items():
            # Check if names are similar
            if name_lower in db_name or db_name in name_lower:
                return url
        
        # Strategy 3: Generate slug and check mapping
        slug = self._name_to_slug(assessment_name)
        
        if slug in self._url_map:
            return self._url_map[slug]
        
        # Try with "-new" suffix
        if f"{slug}-new" in self._url_map:
            return self._url_map[f"{slug}-new"]
        
        # Try without common suffixes
        for suffix in ['-test', '-assessment', '-solution', '-new']:
            if slug.endswith(suffix):
                base_slug = slug[:-len(suffix)]
                if base_slug in self._url_map:
                    return self._url_map[base_slug]
        
        # Strategy 4: Generate URL as fallback
        base_url = "https://www.shl.com/solutions/products/product-catalog/view/"
        return f"{base_url}{slug}/"
    
    def _name_to_slug(self, name: str) -> str:
        """Convert assessment name to URL slug"""
        slug = name.lower()
        slug = slug.replace(' ', '-').replace('_', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        slug = re.sub(r'-+', '-', slug)  # Remove multiple hyphens
        slug = slug.strip('-')
        return slug
    
    def get_all_urls(self) -> Dict[str, str]:
        """Get all URL mappings (slug -> URL)"""
        return self._url_map.copy()
    
    def refresh(self):
        """Refresh URL mappings from database"""
        log.info("Refreshing URL mappings from Supabase...")
        self._url_map.clear()
        self._name_to_url.clear()
        self._load_url_mapping()


# Global instance
_url_mapper: Optional[AssessmentURLMapper] = None


def get_url_mapper() -> AssessmentURLMapper:
    """Get the global URL mapper instance"""
    global _url_mapper
    if _url_mapper is None:
        _url_mapper = AssessmentURLMapper()
    return _url_mapper


def refresh_url_mapper():
    """Refresh the global URL mapper from database"""
    global _url_mapper
    if _url_mapper is not None:
        _url_mapper.refresh()
    else:
        _url_mapper = AssessmentURLMapper()

