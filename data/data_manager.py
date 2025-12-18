"""
Data loader and manager for SHL Assessment catalogue
"""
import json
from typing import List, Dict, Optional
from pathlib import Path
from models.schemas import Assessment, TestType


class DataManager:
    """Manages assessment data loading and querying"""
    
    def __init__(self, data_path: str = "data/shl_products.json"):
        self.data_path = Path(data_path)
        self.assessments: List[Assessment] = []
        self.load_data()
    
    def load_data(self) -> None:
        """Load assessment data from JSON file"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load pre-packaged solutions
        for item in data.get('pre_packaged_solutions', []):
            self.assessments.append(Assessment(**item))
        
        # Load individual test solutions
        for item in data.get('individual_test_solutions', []):
            self.assessments.append(Assessment(**item))
        
        print(f"✓ Loaded {len(self.assessments)} assessments")
    
    def get_all_assessments(self) -> List[Assessment]:
        """Get all assessments"""
        return self.assessments
    
    def get_assessment_by_id(self, assessment_id: str) -> Optional[Assessment]:
        """Get specific assessment by ID"""
        for assessment in self.assessments:
            if assessment.id == assessment_id:
                return assessment
        return None
    
    def filter_by_job_family(self, job_family: str) -> List[Assessment]:
        """Filter assessments by job family"""
        return [a for a in self.assessments if a.job_family and job_family.lower() in a.job_family.lower()]
    
    def filter_by_industry(self, industry: str) -> List[Assessment]:
        """Filter assessments by industry"""
        return [a for a in self.assessments 
                if any(industry.lower() in ind.lower() for ind in a.industries)]
    
    def filter_by_test_types(self, test_types: List[TestType]) -> List[Assessment]:
        """Filter assessments by test types"""
        return [a for a in self.assessments 
                if any(tt in a.test_types for tt in test_types)]
    
    def get_unique_job_families(self) -> List[str]:
        """Get list of unique job families"""
        families = set()
        for a in self.assessments:
            if a.job_family:
                families.add(a.job_family)
        return sorted(list(families))
    
    def get_unique_industries(self) -> List[str]:
        """Get list of unique industries"""
        industries = set()
        for a in self.assessments:
            industries.update(a.industries)
        return sorted(list(industries))
    
    def get_unique_skills(self) -> List[str]:
        """Get list of unique skills"""
        skills = set()
        for a in self.assessments:
            skills.update(a.skills)
        return sorted(list(skills))
    
    def export_to_csv(self, output_path: str = "data/assessments.csv") -> None:
        """Export assessments to CSV format"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not self.assessments:
                return
            
            fieldnames = ['id', 'name', 'type', 'test_types', 'job_family', 
                         'job_level', 'industries', 'skills', 'duration']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for assessment in self.assessments:
                writer.writerow({
                    'id': assessment.id,
                    'name': assessment.name,
                    'type': assessment.type,
                    'test_types': ','.join(assessment.test_types),
                    'job_family': assessment.job_family or '',
                    'job_level': assessment.job_level or '',
                    'industries': ','.join(assessment.industries),
                    'skills': ','.join(assessment.skills),
                    'duration': assessment.duration or ''
                })
        
        print(f"✓ Exported to {output_path}")


if __name__ == "__main__":
    # Test the data manager
    dm = DataManager()
    print(f"\nTotal Assessments: {len(dm.get_all_assessments())}")
    print(f"Job Families: {dm.get_unique_job_families()}")
    print(f"Industries: {dm.get_unique_industries()}")
    print(f"Total Skills: {len(dm.get_unique_skills())}")
