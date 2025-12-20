"""
URL extractor utility for fetching and extracting text from job description URLs
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def extract_text_from_url(url: str, timeout: int = 10) -> str:
    """
    Fetch URL and extract job description text
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Extracted text content from the URL
        
    Raises:
        ValueError: If URL is invalid or cannot be fetched
    """
    try:
        # Fetch URL content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract text from main content areas
        # Try common content containers first
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.job-description']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.body
        
        if not main_content:
            raise ValueError("Could not extract content from URL")
        
        # Get text and clean it
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        if not text or len(text) < 50:
            raise ValueError("Extracted text is too short or empty")
        
        logger.info(f"Successfully extracted {len(text)} characters from {url}")
        return text
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        raise ValueError(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to extract text from {url}: {str(e)}")
        raise ValueError(f"Failed to extract text from URL: {str(e)}")


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL
    
    Args:
        url: String to check
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
