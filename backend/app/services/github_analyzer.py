"""
GitHub Profile Analyzer - Extracts skills and experience from GitHub profiles
"""
import re
import httpx
from typing import Dict, List, Optional
from app.core.logging import log


class GitHubAnalyzer:
    """
    Analyzes GitHub profiles to extract programming languages, skills, and activity
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub analyzer"""
        self.github_token = github_token
        self.api_base = "https://api.github.com"
        
        # Language to skill mapping
        self.language_skills = {
            'Python': ['Python', 'Django', 'Flask', 'FastAPI', 'Data Science', 'Machine Learning'],
            'JavaScript': ['JavaScript', 'Node.js', 'React', 'Vue', 'Angular', 'Web Development'],
            'TypeScript': ['TypeScript', 'React', 'Angular', 'Node.js', 'Web Development'],
            'Java': ['Java', 'Spring', 'Hibernate', 'Maven', 'Enterprise Development'],
            'C++': ['C++', 'System Programming', 'Performance Optimization'],
            'C#': ['C#', '.NET', 'ASP.NET', 'Azure'],
            'Go': ['Go', 'Microservices', 'Cloud Native', 'Backend Development'],
            'Rust': ['Rust', 'System Programming', 'WebAssembly'],
            'Ruby': ['Ruby', 'Rails', 'Web Development'],
            'PHP': ['PHP', 'Laravel', 'WordPress', 'Web Development'],
            'Swift': ['Swift', 'iOS', 'Mobile Development'],
            'Kotlin': ['Kotlin', 'Android', 'Mobile Development'],
            'HTML': ['HTML', 'CSS', 'Web Development', 'Frontend'],
            'CSS': ['CSS', 'Sass', 'Frontend', 'Web Design'],
            'SQL': ['SQL', 'Database', 'MySQL', 'PostgreSQL'],
            'Shell': ['DevOps', 'Automation', 'Linux', 'System Administration']
        }
    
    async def analyze_profile(self, github_url: str) -> Dict:
        """
        Analyze GitHub profile and extract information
        
        Args:
            github_url: GitHub profile URL (e.g., https://github.com/username)
            
        Returns:
            Dictionary with extracted skills and experience
        """
        log.info(f"Analyzing GitHub profile: {github_url}")
        
        try:
            # Extract username from URL
            username = self._extract_username(github_url)
            if not username:
                log.warning("Could not extract username from GitHub URL")
                return self._empty_result()
            
            # Fetch user data and repositories
            user_data = await self._fetch_user_data(username)
            repos = await self._fetch_repositories(username)
            
            if not user_data or not repos:
                log.warning("Failed to fetch GitHub data")
                return self._empty_result()
            
            # Analyze data
            result = {
                'skills': self._extract_skills_from_repos(repos),
                'languages': self._extract_languages(repos),
                'total_repos': len(repos),
                'total_stars': sum(repo.get('stargazers_count', 0) for repo in repos),
                'contributions': user_data.get('public_repos', 0),
                'bio': user_data.get('bio', ''),
                'job_level': self._determine_experience_level(user_data, repos),
                'specializations': self._determine_specializations(repos)
            }
            
            log.info(f"✅ Extracted from GitHub: {len(result['skills'])} skills, {len(result['languages'])} languages, level: {result['job_level']}")
            return result
            
        except Exception as e:
            log.error(f"GitHub analysis error: {e}")
            return self._empty_result()
    
    def _extract_username(self, github_url: str) -> Optional[str]:
        """Extract username from GitHub URL"""
        patterns = [
            r'github\.com/([^/]+)/?$',
            r'github\.com/([^/]+)/.*'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, github_url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_user_data(self, username: str) -> Optional[Dict]:
        """Fetch user data from GitHub API"""
        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/users/{username}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    log.warning(f"GitHub API returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            log.error(f"Error fetching user data: {e}")
            return None
    
    async def _fetch_repositories(self, username: str) -> List[Dict]:
        """Fetch user repositories from GitHub API"""
        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/users/{username}/repos",
                    headers=headers,
                    params={'per_page': 100, 'sort': 'updated'},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    log.warning(f"GitHub API returned status {response.status_code}")
                    return []
                    
        except Exception as e:
            log.error(f"Error fetching repositories: {e}")
            return []
    
    def _extract_languages(self, repos: List[Dict]) -> List[str]:
        """Extract programming languages from repositories"""
        languages = set()
        
        for repo in repos:
            lang = repo.get('language')
            if lang:
                languages.add(lang)
        
        return sorted(list(languages))
    
    def _extract_skills_from_repos(self, repos: List[Dict]) -> List[str]:
        """Extract skills based on repository languages and topics"""
        skills = set()
        
        # Extract from languages
        for repo in repos:
            lang = repo.get('language')
            if lang and lang in self.language_skills:
                skills.update(self.language_skills[lang])
            
            # Extract from topics/tags
            topics = repo.get('topics', [])
            for topic in topics:
                if any(tech in topic.lower() for tech in ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'docker', 'kubernetes']):
                    skills.add(topic.title())
            
            # Extract from repo names and descriptions
            name = repo.get('name', '').lower()
            desc = repo.get('description', '').lower() if repo.get('description') else ''
            
            # Common frameworks and tools
            keywords = ['docker', 'kubernetes', 'aws', 'azure', 'react', 'vue', 'angular', 'django', 'flask', 'spring', 'tensorflow', 'pytorch']
            for keyword in keywords:
                if keyword in name or keyword in desc:
                    skills.add(keyword.title())
        
        return sorted(list(skills))
    
    def _determine_experience_level(self, user_data: Dict, repos: List[Dict]) -> str:
        """Determine experience level based on GitHub activity"""
        total_repos = user_data.get('public_repos', 0)
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
        followers = user_data.get('followers', 0)
        
        # Calculate experience score
        score = 0
        score += min(total_repos / 10, 3)  # Max 3 points for repos
        score += min(total_stars / 50, 2)  # Max 2 points for stars
        score += min(followers / 20, 2)    # Max 2 points for followers
        
        if score >= 5:
            return 'Senior Level'
        elif score >= 3:
            return 'Mid Level'
        else:
            return 'Entry Level'
    
    def _determine_specializations(self, repos: List[Dict]) -> List[str]:
        """Determine technical specializations from repositories"""
        specializations = set()
        
        # Count repos by category
        categories = {
            'Web Development': ['website', 'web', 'frontend', 'backend', 'fullstack'],
            'Mobile Development': ['android', 'ios', 'mobile', 'app'],
            'Data Science': ['data', 'analysis', 'visualization', 'analytics', 'ml', 'machine-learning'],
            'Machine Learning': ['ml', 'ai', 'deep-learning', 'neural', 'tensorflow', 'pytorch'],
            'DevOps': ['devops', 'ci-cd', 'docker', 'kubernetes', 'terraform', 'deployment'],
            'Cloud': ['aws', 'azure', 'gcp', 'cloud'],
            'Game Development': ['game', 'unity', 'unreal', 'gamedev']
        }
        
        category_scores = {cat: 0 for cat in categories}
        
        for repo in repos:
            name = repo.get('name', '').lower()
            desc = repo.get('description', '').lower() if repo.get('description') else ''
            topics = ' '.join(repo.get('topics', [])).lower()
            
            combined_text = f"{name} {desc} {topics}"
            
            for category, keywords in categories.items():
                if any(keyword in combined_text for keyword in keywords):
                    category_scores[category] += 1
        
        # Get top specializations
        for category, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 2:  # At least 2 repos in this category
                specializations.add(category)
                if len(specializations) >= 3:
                    break
        
        return sorted(list(specializations))
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'skills': [],
            'languages': [],
            'total_repos': 0,
            'total_stars': 0,
            'contributions': 0,
            'bio': '',
            'job_level': 'Entry Level',
            'specializations': []
        }
