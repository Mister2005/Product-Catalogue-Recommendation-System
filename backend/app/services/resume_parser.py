"""
Resume Parser - Extracts key information from PDF/DOC resumes
"""
import re
from typing import Dict, List, Optional
import PyPDF2
import io
from app.core.logging import log


class ResumeParser:
    """
    Intelligent resume parser to extract skills, experience, and job information
    """
    
    def __init__(self):
        """Initialize resume parser with skill patterns"""
        # Common technical skills
        self.tech_skills = {
            'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express', 'next.js', 'nuxt'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd'],
            'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'data science', 'machine learning', 'deep learning', 'nlp', 'computer vision'],
            'soft_skills': ['leadership', 'communication', 'problem solving', 'teamwork', 'analytical', 'critical thinking', 'agile', 'scrum']
        }
        
        # Job level indicators
        self.level_patterns = {
            'Entry Level': ['intern', 'junior', 'entry', 'graduate', 'trainee', 'associate'],
            'Mid Level': ['mid', 'intermediate', 'experienced', '3-5 years', '2-4 years'],
            'Senior Level': ['senior', 'lead', 'principal', 'expert', '5+ years', '7+ years'],
            'Executive': ['director', 'vp', 'cto', 'ceo', 'head of', 'chief', 'manager']
        }
        
        # Industry keywords
        self.industry_patterns = {
            'Technology': ['software', 'tech', 'it', 'engineering', 'developer', 'programmer'],
            'Finance': ['finance', 'banking', 'investment', 'trading', 'fintech'],
            'Healthcare': ['healthcare', 'medical', 'hospital', 'pharma', 'clinical'],
            'Retail': ['retail', 'e-commerce', 'sales', 'customer service'],
            'Manufacturing': ['manufacturing', 'production', 'supply chain', 'operations']
        }
    
    async def parse_resume(self, file_content: bytes, filename: str) -> Dict:
        """
        Parse resume and extract key information
        
        Args:
            file_content: Binary content of the resume file
            filename: Name of the file
            
        Returns:
            Dictionary with extracted information
        """
        log.info(f"Parsing resume: {filename}")
        
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(file_content)
            
            if not text or len(text) < 50:
                log.warning("Resume text extraction failed or too short")
                return self._empty_result()
            
            # Extract information
            result = {
                'skills': self._extract_skills(text),
                'job_title': self._extract_job_title(text),
                'job_level': self._extract_job_level(text),
                'industry': self._extract_industry(text),
                'years_of_experience': self._extract_experience_years(text),
                'education': self._extract_education(text),
                'certifications': self._extract_certifications(text)
            }
            
            log.info(f"✅ Extracted from resume: {len(result['skills'])} skills, job_level: {result['job_level']}, industry: {result['industry']}")
            return result
            
        except Exception as e:
            log.error(f"Resume parsing error: {e}")
            return self._empty_result()
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.lower()
        except Exception as e:
            log.error(f"PDF text extraction error: {e}")
            return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and soft skills from text"""
        found_skills = set()
        
        # Search for all skill categories
        for category, skills in self.tech_skills.items():
            for skill in skills:
                # Use word boundaries for accurate matching
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    # Capitalize properly
                    found_skills.add(skill.title() if len(skill) > 3 else skill.upper())
        
        return sorted(list(found_skills))
    
    def _extract_job_title(self, text: str) -> Optional[str]:
        """Extract most likely job title from resume"""
        # Common job title patterns
        title_patterns = [
            r'(?:software|web|frontend|backend|full[-\s]?stack|data|machine learning|devops|cloud)\s+(?:engineer|developer|architect)',
            r'(?:senior|junior|lead|principal)\s+(?:engineer|developer|programmer)',
            r'(?:product|project|program)\s+manager',
            r'(?:data|business)\s+analyst',
            r'(?:ui|ux)\s+designer'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).title()
        
        return None
    
    def _extract_job_level(self, text: str) -> str:
        """Determine job level from resume"""
        for level, keywords in self.level_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        
        return 'Mid Level'  # Default
    
    def _extract_industry(self, text: str) -> Optional[str]:
        """Extract industry from resume"""
        industry_scores = {}
        
        for industry, keywords in self.industry_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        
        return None
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience from resume"""
        # Pattern: "X years of experience"
        pattern = r'(\d+)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            return max(int(match) for match in matches)
        
        return None
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education degrees"""
        degrees = []
        degree_patterns = [
            r'\b(?:bachelor|bs|ba|bsc|btech|be)\b',
            r'\b(?:master|ms|ma|msc|mtech|mba|me)\b',
            r'\b(?:phd|doctorate)\b'
        ]
        
        for pattern in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                degrees.append(pattern.strip('\\b'))
        
        return degrees
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract professional certifications"""
        cert_patterns = [
            r'\b(?:aws|azure|gcp)\s+certified\b',
            r'\b(?:pmp|scrum|agile)\s+certified\b',
            r'\bcertified\s+(?:kubernetes|docker|jenkins)\b'
        ]
        
        certifications = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend([m.title() for m in matches])
        
        return certifications
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'skills': [],
            'job_title': None,
            'job_level': 'Entry Level',
            'industry': None,
            'years_of_experience': None,
            'education': [],
            'certifications': []
        }
