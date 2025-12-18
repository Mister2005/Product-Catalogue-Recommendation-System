"""
Web scraper for SHL Product Catalogue
This module can be extended to scrape live data from the SHL website
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import time


class SHLScraper:
    """Scraper for SHL product catalogue website"""
    
    BASE_URL = "https://www.shl.com/products/product-catalog/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_catalogue_page(self) -> Optional[str]:
        """Fetch the main catalogue page HTML"""
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching catalogue: {e}")
            return None
    
    def parse_assessment_table(self, html: str) -> List[Dict]:
        """Parse assessment data from HTML tables"""
        soup = BeautifulSoup(html, 'html.parser')
        assessments = []
        
        # Find all assessment tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    name = cols[0].get_text(strip=True)
                    remote_testing = bool(cols[1].find('img'))
                    adaptive = bool(cols[2].find('img'))
                    test_types_text = cols[3].get_text(strip=True)
                    
                    # Parse test types
                    test_types = [t.strip() for t in test_types_text.split() if t.strip()]
                    
                    assessment = {
                        'name': name,
                        'remote_testing': remote_testing,
                        'adaptive': adaptive,
                        'test_types': test_types
                    }
                    assessments.append(assessment)
        
        return assessments
    
    def enrich_assessment_data(self, assessments: List[Dict]) -> List[Dict]:
        """Enrich basic assessment data with additional information"""
        # This can be extended to make additional API calls or scrape detail pages
        for assessment in assessments:
            # Generate ID from name
            assessment['id'] = assessment['name'].lower().replace(' ', '_').replace('-', '_')
            
            # Add placeholder fields that would be scraped from detail pages
            assessment['description'] = f"Assessment for {assessment['name']}"
            assessment['industries'] = []
            assessment['languages'] = ['English']
            assessment['skills'] = []
            assessment['duration'] = None
        
        return assessments
    
    def scrape_and_save(self, output_path: str = "data/scraped_products.json"):
        """Main scraping workflow"""
        print("🔍 Fetching SHL product catalogue...")
        html = self.fetch_catalogue_page()
        
        if not html:
            print("❌ Failed to fetch catalogue page")
            return
        
        print("📊 Parsing assessment data...")
        assessments = self.parse_assessment_table(html)
        
        print("✨ Enriching data...")
        assessments = self.enrich_assessment_data(assessments)
        
        print(f"💾 Saving {len(assessments)} assessments to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'assessments': assessments}, f, indent=2)
        
        print("✅ Scraping complete!")
        return assessments


def scrape_shl_catalogue():
    """Convenience function to run the scraper"""
    scraper = SHLScraper()
    return scraper.scrape_and_save()


if __name__ == "__main__":
    scrape_shl_catalogue()
