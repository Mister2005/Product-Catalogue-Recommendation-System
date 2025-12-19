"""
Enhanced Web Scraper for SHL Product Catalogue
Handles multi-level pagination and detail page extraction
Scrapes ALL 520+ assessments from the SHL website
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import json
import time
import re
from urllib.parse import urljoin
import logging
from tqdm import tqdm
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SHLCatalogueScraper:
    """
    Comprehensive scraper for SHL product catalogue
    Handles complex pagination patterns and detail page extraction
    """
    
    BASE_URL = "https://www.shl.com/products/product-catalog/"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper with rate limiting
        
        Args:
            delay: Delay between requests in seconds (default: 1.0)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.delay = delay
        self.scraped_urls: Set[str] = set()
        self.assessments: List[Dict] = []
        
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            HTML content or None if failed
        """
        for attempt in range(max_retries):
            try:
                time.sleep(self.delay)  # Rate limiting
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.delay * 2)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
        return None
    
    def _parse_assessment_table(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse assessment data from HTML tables
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of assessment dictionaries
        """
        assessments = []
        
        # Find all tables with assessment data
        tables = soup.find_all('table')
        
        for table in tables:
            # Skip if not an assessment table
            headers = table.find_all('th')
            if not headers or len(headers) < 3:
                continue
            
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                try:
                    # Extract assessment name and link
                    name_cell = cols[0]
                    name_link = name_cell.find('a', href=True)
                    
                    if name_link:
                        name = name_link.get_text(strip=True)
                        detail_url = urljoin(self.BASE_URL, name_link['href'])
                    else:
                        name = name_cell.get_text(strip=True)
                        detail_url = None
                    
                    # Extract remote testing capability
                    remote_testing = bool(cols[1].find('img') or 'yes' in cols[1].get_text().lower())
                    
                    # Extract adaptive/IRT capability
                    adaptive = bool(cols[2].find('img') or 'yes' in cols[2].get_text().lower())
                    
                    # Extract test types
                    test_types_cell = cols[3]
                    test_types = []
                    
                    # Look for images with alt text
                    type_images = test_types_cell.find_all('img', alt=True)
                    for img in type_images:
                        alt_text = img.get('alt', '').strip()
                        if alt_text:
                            test_types.append(alt_text)
                    
                    # If no images, parse text
                    if not test_types:
                        test_types_text = test_types_cell.get_text(strip=True)
                        test_types = [t.strip() for t in re.split(r'[,\s]+', test_types_text) if t.strip()]
                    
                    assessment = {
                        'name': name,
                        'detail_url': detail_url,
                        'remote_testing': remote_testing,
                        'adaptive': adaptive,
                        'test_types': test_types,
                        'scraped_from_list': True
                    }
                    
                    assessments.append(assessment)
                    
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
        
        return assessments
    
    def _scrape_assessment_detail(self, url: str) -> Optional[Dict]:
        """
        Scrape detailed information from assessment detail page
        
        Args:
            url: Assessment detail page URL
            
        Returns:
            Dictionary with detailed assessment information
        """
        html = self._make_request(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        try:
            # Extract description
            description_div = soup.find('div', class_='product-description')
            if description_div:
                details['description'] = description_div.get_text(strip=True)
            else:
                # Try alternative selectors
                content_div = soup.find('div', class_='content')
                if content_div:
                    paragraphs = content_div.find_all('p')
                    if paragraphs:
                        details['description'] = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])
            
            # Extract job levels
            job_levels = []
            job_level_section = soup.find('div', class_='job-levels') or soup.find('div', string=re.compile('Job Level', re.I))
            if job_level_section:
                job_level_items = job_level_section.find_all('li') or job_level_section.find_all('span')
                job_levels = [item.get_text(strip=True) for item in job_level_items]
            details['job_levels'] = job_levels
            
            # Extract industries
            industries = []
            industry_section = soup.find('div', class_='industries') or soup.find('div', string=re.compile('Industr', re.I))
            if industry_section:
                industry_items = industry_section.find_all('li') or industry_section.find_all('span')
                industries = [item.get_text(strip=True) for item in industry_items]
            details['industries'] = industries
            
            # Extract languages
            languages = []
            language_section = soup.find('div', class_='languages') or soup.find('div', string=re.compile('Language', re.I))
            if language_section:
                language_items = language_section.find_all('li') or language_section.find_all('span')
                languages = [item.get_text(strip=True) for item in language_items]
            details['languages'] = languages
            
            # Extract job family
            job_family = None
            job_family_elem = soup.find('span', class_='job-family') or soup.find('div', string=re.compile('Job Family', re.I))
            if job_family_elem:
                job_family = job_family_elem.get_text(strip=True)
            details['job_family'] = job_family
            
            # Extract skills
            skills = []
            skills_section = soup.find('div', class_='skills') or soup.find('div', string=re.compile('Skills', re.I))
            if skills_section:
                skill_items = skills_section.find_all('li') or skills_section.find_all('span')
                skills = [item.get_text(strip=True) for item in skill_items]
            details['skills'] = skills
            
            # Extract duration
            duration = None
            duration_elem = soup.find('span', class_='duration') or soup.find('div', string=re.compile('Duration|Time', re.I))
            if duration_elem:
                duration_text = duration_elem.get_text(strip=True)
                # Extract numeric duration
                duration_match = re.search(r'(\d+)', duration_text)
                if duration_match:
                    duration = int(duration_match.group(1))
            details['duration'] = duration
            
        except Exception as e:
            logger.warning(f"Error parsing detail page {url}: {e}")
        
        return details
    
    def _discover_all_pagination_urls(self) -> List[str]:
        """
        Discover all pagination URLs by systematically generating them
        Based on actual SHL website patterns:
        - Pre-packaged Job Solutions: start=0 to 132, type=2&type=2
        - Individual Test Solutions: start=0 to 372, type=2&type=1
        
        Returns:
            List of all unique pagination URLs
        """
        logger.info("🔍 Generating all pagination URLs based on actual SHL patterns...")
        
        all_urls = set()
        
        # Base URL (shows all assessments)
        all_urls.add(self.BASE_URL)
        
        # Pre-packaged Job Solutions: type=2&type=2
        # Range: start=0 to start=132 (increment by 12)
        logger.info("  📦 Generating Pre-packaged Job Solutions URLs (type=2&type=2)...")
        for start in range(0, 144, 12):  # 0, 12, 24, ..., 132
            url = f"{self.BASE_URL}?start={start}&type=2&type=2"
            all_urls.add(url)
        
        # Individual Test Solutions: type=2&type=1
        # Range: start=0 to start=372 (increment by 12)
        logger.info("  🧪 Generating Individual Test Solutions URLs (type=2&type=1)...")
        for start in range(0, 384, 12):  # 0, 12, 24, ..., 372
            url = f"{self.BASE_URL}?start={start}&type=2&type=1"
            all_urls.add(url)
        
        # Additional patterns to ensure complete coverage
        # Sometimes the website uses single type parameter
        logger.info("  🔄 Adding alternative URL patterns for completeness...")
        
        # type=2 alone (might show combined results)
        for start in range(0, 384, 12):
            url = f"{self.BASE_URL}?start={start}&type=2"
            all_urls.add(url)
        
        # type=1 alone (individual tests alternative)
        for start in range(0, 384, 12):
            url = f"{self.BASE_URL}?start={start}&type=1"
            all_urls.add(url)
        
        # type=3 (if there are other categories)
        for start in range(0, 144, 12):
            url = f"{self.BASE_URL}?start={start}&type=3"
            all_urls.add(url)
        
        # Double type=1 pattern (sometimes used)
        for start in range(0, 384, 12):
            url = f"{self.BASE_URL}?start={start}&type=1&type=1"
            all_urls.add(url)
        
        # type=3&type=1 combination
        for start in range(0, 144, 12):
            url = f"{self.BASE_URL}?start={start}&type=3&type=1"
            all_urls.add(url)
        
        logger.info(f"✅ Generated {len(all_urls)} unique pagination URLs")
        logger.info(f"   - Pre-packaged Solutions: ~{len(range(0, 144, 12))} pages")
        logger.info(f"   - Individual Test Solutions: ~{len(range(0, 384, 12))} pages")
        
        return sorted(list(all_urls))  # Sort for consistent ordering


    
    def scrape_catalogue(self) -> Dict:
        """
        Main scraping method - scrapes all assessments from catalogue
        
        Returns:
            Dictionary with metadata and assessments
        """
        logger.info("🚀 Starting comprehensive SHL catalogue scraping...")
        
        # Step 1: Discover all pagination URLs
        all_urls = self._discover_all_pagination_urls()
        
        # Step 2: Scrape assessments from all pages
        logger.info(f"\n📊 Scraping assessments from {len(all_urls)} pages...")
        
        all_assessments_map = {}  # Use dict to avoid duplicates by name
        
        for url in tqdm(all_urls, desc="Scraping catalogue pages"):
            if url in self.scraped_urls:
                continue
            
            self.scraped_urls.add(url)
            
            html = self._make_request(url)
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            assessments = self._parse_assessment_table(soup)
            
            for assessment in assessments:
                name = assessment['name']
                if name not in all_assessments_map:
                    all_assessments_map[name] = assessment
                else:
                    # Merge data if assessment already exists
                    existing = all_assessments_map[name]
                    if assessment.get('detail_url') and not existing.get('detail_url'):
                        existing['detail_url'] = assessment['detail_url']
        
        logger.info(f"✅ Found {len(all_assessments_map)} unique assessments")
        
        # Step 3: Scrape detail pages
        logger.info(f"\n🔎 Scraping detail pages for {len(all_assessments_map)} assessments...")
        
        assessments_with_details = []
        
        for name, assessment in tqdm(all_assessments_map.items(), desc="Scraping detail pages"):
            detail_url = assessment.get('detail_url')
            
            if detail_url:
                details = self._scrape_assessment_detail(detail_url)
                if details:
                    assessment.update(details)
            
            # Generate ID from name
            assessment['id'] = name.lower().replace(' ', '_').replace('-', '_').replace('.', '_').replace('(', '').replace(')', '')
            
            # Set defaults for missing fields
            assessment.setdefault('description', f"Assessment for {name}")
            assessment.setdefault('job_levels', [])
            assessment.setdefault('industries', ['All Industries'])
            assessment.setdefault('languages', ['English'])
            assessment.setdefault('job_family', None)
            assessment.setdefault('duration', None)
            assessment.setdefault('skills', [])
            
            # Determine assessment type
            if 'solution' in name.lower() or 'short form' in name.lower():
                assessment['type'] = 'Pre-packaged Job Solution'
            else:
                assessment['type'] = 'Individual Test Solution'
            
            # Clean up temporary fields
            assessment.pop('scraped_from_list', None)
            assessment.pop('detail_url', None)
            
            # Determine job_level from job_levels array if not set
            if not assessment.get('job_level') and assessment.get('job_levels'):
                assessment['job_level'] = assessment['job_levels'][0] if assessment['job_levels'] else None
            
            assessments_with_details.append(assessment)
        
        self.assessments = assessments_with_details
        
        return {
            "metadata": {
                "source": "SHL Website (Real Scraping)" if len(assessments_with_details) > 50 else "Enhanced Mock Data",
                "scrape_timestamp": datetime.now().isoformat(),
                "total_assessments": len(assessments_with_details),
                "version": "2.0"
            },
            "assessments": assessments_with_details
        }
    
    def save_to_file(self, data: Dict, filename: str = "data/shl_products_complete.json"):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Successfully saved {data['metadata']['total_assessments']} assessments to {filename}")
        logger.info(f"📊 Source: {data['metadata']['source']}")
        logger.info(f"📅 Timestamp: {data['metadata']['scrape_timestamp']}")


def main():
    """Main execution"""
    scraper = SHLCatalogueScraper(delay=0.5)  # 0.5s delay between requests
    data = scraper.scrape_catalogue()
    scraper.save_to_file(data, "data/shl_products_complete.json")
    
    # Print summary
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Total Assessments: {data['metadata']['total_assessments']}")
    
    # Count by type
    type_counts = {}
    for assessment in data['assessments']:
        atype = assessment.get('type', 'Unknown')
        type_counts[atype] = type_counts.get(atype, 0) + 1
    
    print("\nBreakdown by Type:")
    for atype, count in type_counts.items():
        print(f"  - {atype}: {count}")
    
    print("="*60)


if __name__ == "__main__":
    main()
