"""
SHL Website URL Scraper
Scrapes assessment URLs from SHL product catalog website
"""
import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class SHLURLScraper:
    """Scrapes assessment URLs from SHL website"""
    
    BASE_URL = "https://www.shl.com"
    CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper
        
        Args:
            delay: Delay between requests in seconds (to avoid rate limiting)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_catalog_page(self, url: str) -> List[Dict[str, str]]:
        """
        Scrape a single catalog page for assessment links
        
        Args:
            url: URL of the catalog page
            
        Returns:
            List of dicts with 'name' and 'url' keys
        """
        try:
            log.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            assessments = []
            
            # Find all assessment links
            # SHL uses different patterns, try multiple selectors
            selectors = [
                'a[href*="/product-catalog/view/"]',
                '.product-item a',
                '.assessment-link',
                'a.product-name'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    log.info(f"Found {len(links)} links with selector: {selector}")
                    break
            
            for link in links:
                href = link.get('href')
                if href and '/view/' in href:
                    # Get full URL
                    full_url = urljoin(self.BASE_URL, href)
                    
                    # Extract slug from URL
                    slug_match = re.search(r'/view/([^/]+)/?$', full_url)
                    if slug_match:
                        slug = slug_match.group(1)
                        
                        # Get assessment name from link text or title
                        name = link.get_text(strip=True) or link.get('title', '')
                        
                        if name and slug:
                            assessments.append({
                                'name': name,
                                'url': full_url,
                                'slug': slug
                            })
            
            log.info(f"Extracted {len(assessments)} assessment URLs")
            time.sleep(self.delay)  # Rate limiting
            
            return assessments
            
        except Exception as e:
            log.error(f"Error scraping {url}: {e}")
            return []
    
    def scrape_all_assessments(self) -> List[Dict[str, str]]:
        """
        Scrape all assessment URLs from SHL catalog
        
        Returns:
            List of assessment dicts with name, url, and slug
        """
        log.info("Starting SHL catalog scraping...")
        all_assessments = []
        
        # Try to scrape the main catalog page
        assessments = self.scrape_catalog_page(self.CATALOG_URL)
        all_assessments.extend(assessments)
        
        # Try to find pagination or category pages
        # This is a placeholder - actual implementation depends on SHL website structure
        try:
            response = self.session.get(self.CATALOG_URL, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination links
            pagination_links = soup.select('a.page-link, a.pagination-link, .pagination a')
            for link in pagination_links[:10]:  # Limit to avoid too many requests
                href = link.get('href')
                if href:
                    page_url = urljoin(self.BASE_URL, href)
                    page_assessments = self.scrape_catalog_page(page_url)
                    all_assessments.extend(page_assessments)
        
        except Exception as e:
            log.warning(f"Could not scrape pagination: {e}")
        
        # Remove duplicates based on URL
        unique_assessments = {}
        for assessment in all_assessments:
            url = assessment['url']
            if url not in unique_assessments:
                unique_assessments[url] = assessment
        
        result = list(unique_assessments.values())
        log.info(f"Total unique assessments scraped: {len(result)}")
        
        return result
    
    def verify_url(self, url: str) -> bool:
        """
        Verify that a URL returns a valid page
        
        Args:
            url: URL to verify
            
        Returns:
            True if URL is valid (returns 200), False otherwise
        """
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False


def generate_url_from_name(name: str) -> tuple[str, str]:
    """
    Generate SHL catalog URL from assessment name
    
    Args:
        name: Assessment name
        
    Returns:
        Tuple of (url, slug)
    """
    # Convert name to slug
    slug = name.lower()
    slug = slug.replace(' ', '-').replace('_', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Remove multiple hyphens
    slug = slug.strip('-')
    
    # Try with and without "new" suffix
    base_url = "https://www.shl.com/solutions/products/product-catalog/view/"
    url = f"{base_url}{slug}/"
    
    return url, slug


if __name__ == "__main__":
    # Test scraper
    scraper = SHLURLScraper()
    assessments = scraper.scrape_all_assessments()
    
    print(f"\nScraped {len(assessments)} assessments:")
    for i, assessment in enumerate(assessments[:10], 1):
        print(f"{i}. {assessment['name']}: {assessment['url']}")
    
    if assessments:
        print(f"\n... and {len(assessments) - 10} more")
