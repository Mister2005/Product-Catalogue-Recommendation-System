"""
PDF text extraction utility
Extracts text from PDF files for job description analysis
"""
from pathlib import Path
from typing import Optional
import PyPDF2
import io
from app.core.logging import log


def extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
    """
    Extract text from PDF file content
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        # Create PDF reader from bytes
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_parts = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        
        if not full_text.strip():
            log.warning("PDF extraction resulted in empty text")
            return None
        
        log.info(f"Successfully extracted {len(full_text)} characters from PDF")
        return full_text
        
    except Exception as e:
        log.error(f"Failed to extract text from PDF: {e}")
        return None


def validate_pdf(pdf_content: bytes) -> bool:
    """
    Validate that the content is a valid PDF
    
    Args:
        pdf_content: File content as bytes
        
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        PyPDF2.PdfReader(pdf_file)
        return True
    except:
        return False
