"""
Evaluation module for scraping pipeline
Validates completeness, data quality, and accuracy of scraped assessments
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ScrapingEvaluator:
    """Evaluates the quality and completeness of scraped assessment data"""
    
    # Expected minimum counts based on website inspection
    EXPECTED_MIN_ASSESSMENTS = 500  # Should be 520+
    EXPECTED_PRE_PACKAGED_MIN = 130
    EXPECTED_INDIVIDUAL_MIN = 370
    
    def __init__(self, scraped_data_path: str):
        """
        Initialize evaluator with scraped data
        
        Args:
            scraped_data_path: Path to scraped JSON file
        """
        self.data_path = scraped_data_path
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load scraped data from JSON file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.data_path}: {e}")
            return {}
    
    def evaluate_completeness(self) -> Dict[str, Any]:
        """
        Evaluate completeness of scraped data
        
        Returns:
            Dictionary with completeness metrics
        """
        if not self.data:
            return {
                'score': 0.0,
                'status': 'FAILED',
                'message': 'No data loaded'
            }
        
        metadata = self.data.get('metadata', {})
        total = metadata.get('total_assessments', 0)
        pre_packaged = metadata.get('pre_packaged_solutions', 0)
        individual = metadata.get('individual_test_solutions', 0)
        
        # Calculate completeness score
        total_score = min(total / self.EXPECTED_MIN_ASSESSMENTS, 1.0)
        pre_packaged_score = min(pre_packaged / self.EXPECTED_PRE_PACKAGED_MIN, 1.0)
        individual_score = min(individual / self.EXPECTED_INDIVIDUAL_MIN, 1.0)
        
        overall_score = (total_score + pre_packaged_score + individual_score) / 3
        
        status = 'PASSED' if overall_score >= 0.95 else 'WARNING' if overall_score >= 0.80 else 'FAILED'
        
        return {
            'score': overall_score,
            'status': status,
            'total_assessments': total,
            'expected_min': self.EXPECTED_MIN_ASSESSMENTS,
            'pre_packaged_count': pre_packaged,
            'expected_pre_packaged_min': self.EXPECTED_PRE_PACKAGED_MIN,
            'individual_count': individual,
            'expected_individual_min': self.EXPECTED_INDIVIDUAL_MIN,
            'total_score': total_score,
            'pre_packaged_score': pre_packaged_score,
            'individual_score': individual_score
        }
    
    def evaluate_data_quality(self) -> Dict[str, Any]:
        """
        Evaluate quality of scraped data
        
        Returns:
            Dictionary with quality metrics
        """
        if not self.data:
            return {'score': 0.0, 'status': 'FAILED'}
        
        # Handle new data structure with 'assessments' array
        all_assessments = self.data.get('assessments', [])
        
        # Fallback to old structure if needed
        if not all_assessments:
            all_assessments = (
                self.data.get('pre_packaged_solutions', []) +
                self.data.get('individual_test_solutions', [])
            )
        
        if not all_assessments:
            return {'score': 0.0, 'status': 'FAILED', 'message': 'No assessments found'}
        
        total = len(all_assessments)
        
        # Check required fields
        required_fields = ['id', 'name', 'type', 'test_types']
        optional_fields = ['description', 'job_levels', 'industries', 'languages', 'job_family', 'duration']
        
        required_complete = 0
        has_description = 0
        has_rich_description = 0  # > 50 chars
        has_job_levels = 0
        has_industries = 0
        has_languages = 0
        has_job_family = 0
        has_duration = 0
        has_detail_url = 0
        
        for assessment in all_assessments:
            # Check required fields
            if all(field in assessment and assessment[field] for field in required_fields):
                required_complete += 1
            
            # Check optional fields
            if assessment.get('description'):
                has_description += 1
                if len(assessment['description']) > 50:
                    has_rich_description += 1
            
            if assessment.get('job_levels') and len(assessment['job_levels']) > 0:
                has_job_levels += 1
            
            if assessment.get('industries') and len(assessment['industries']) > 0:
                has_industries += 1
            
            if assessment.get('languages') and len(assessment['languages']) > 0:
                has_languages += 1
            
            if assessment.get('job_family'):
                has_job_family += 1
            
            if assessment.get('duration'):
                has_duration += 1
            
            if assessment.get('detail_url'):
                has_detail_url += 1
        
        # Calculate quality scores
        required_score = required_complete / total
        description_score = has_rich_description / total
        metadata_score = (has_job_levels + has_industries + has_languages) / (total * 3)
        
        overall_score = (required_score * 0.5 + description_score * 0.3 + metadata_score * 0.2)
        
        status = 'PASSED' if overall_score >= 0.90 else 'WARNING' if overall_score >= 0.75 else 'FAILED'
        
        return {
            'score': overall_score,
            'status': status,
            'total_assessments': total,
            'required_fields_complete': required_complete,
            'required_fields_score': required_score,
            'with_description': has_description,
            'with_rich_description': has_rich_description,
            'description_score': description_score,
            'with_job_levels': has_job_levels,
            'with_industries': has_industries,
            'with_languages': has_languages,
            'with_job_family': has_job_family,
            'with_duration': has_duration,
            'with_detail_url': has_detail_url,
            'metadata_score': metadata_score,
            'percentages': {
                'required_complete': f"{required_score * 100:.1f}%",
                'with_rich_description': f"{(has_rich_description / total) * 100:.1f}%",
                'with_job_levels': f"{(has_job_levels / total) * 100:.1f}%",
                'with_industries': f"{(has_industries / total) * 100:.1f}%",
                'with_languages': f"{(has_languages / total) * 100:.1f}%",
            }
        }
    
    def validate_sample(self, sample_size: int = 10) -> Dict[str, Any]:
        """
        Validate a random sample of assessments
        
        Args:
            sample_size: Number of assessments to validate
            
        Returns:
            Dictionary with validation results
        """
        import random
        
        # Handle new data structure with 'assessments' array
        all_assessments = self.data.get('assessments', [])
        
        # Fallback to old structure if needed
        if not all_assessments:
            all_assessments = (
                self.data.get('pre_packaged_solutions', []) +
                self.data.get('individual_test_solutions', [])
            )
        
        if not all_assessments:
            return {'status': 'FAILED', 'message': 'No assessments to validate'}
        
        # Select random sample
        sample = random.sample(all_assessments, min(sample_size, len(all_assessments)))
        
        validation_results = []
        for assessment in sample:
            result = {
                'name': assessment.get('name'),
                'id': assessment.get('id'),
                'has_all_required': all(
                    field in assessment and assessment[field]
                    for field in ['id', 'name', 'type', 'test_types']
                ),
                'description_length': len(assessment.get('description', '')),
                'metadata_completeness': sum([
                    bool(assessment.get('job_levels')),
                    bool(assessment.get('industries')),
                    bool(assessment.get('languages')),
                    bool(assessment.get('job_family')),
                ]) / 4
            }
            validation_results.append(result)
        
        avg_completeness = sum(r['metadata_completeness'] for r in validation_results) / len(validation_results)
        all_valid = all(r['has_all_required'] for r in validation_results)
        
        return {
            'status': 'PASSED' if all_valid and avg_completeness >= 0.7 else 'WARNING',
            'sample_size': len(sample),
            'all_required_fields_present': all_valid,
            'average_metadata_completeness': avg_completeness,
            'sample_results': validation_results
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report
        
        Returns:
            Complete evaluation report
        """
        completeness = self.evaluate_completeness()
        quality = self.evaluate_data_quality()
        sample_validation = self.validate_sample()
        
        # Overall status
        statuses = [completeness['status'], quality['status'], sample_validation['status']]
        if 'FAILED' in statuses:
            overall_status = 'FAILED'
        elif 'WARNING' in statuses:
            overall_status = 'WARNING'
        else:
            overall_status = 'PASSED'
        
        # Overall score
        overall_score = (completeness['score'] + quality['score']) / 2
        
        return {
            'overall_status': overall_status,
            'overall_score': overall_score,
            'completeness': completeness,
            'data_quality': quality,
            'sample_validation': sample_validation,
            'timestamp': self.data.get('metadata', {}).get('scrape_timestamp'),
            'source_file': self.data_path
        }
    
    def print_report(self):
        """Print formatted evaluation report"""
        report = self.generate_report()
        
        print("\n" + "="*70)
        print("📊 SCRAPING EVALUATION REPORT")
        print("="*70)
        
        print(f"\n🎯 Overall Status: {report['overall_status']}")
        print(f"📈 Overall Score: {report['overall_score']:.2%}")
        
        print("\n" + "-"*70)
        print("1️⃣  COMPLETENESS EVALUATION")
        print("-"*70)
        comp = report['completeness']
        print(f"Status: {comp['status']}")
        print(f"Score: {comp['score']:.2%}")
        print(f"Total Assessments: {comp['total_assessments']} (expected: {comp['expected_min']}+)")
        print(f"Pre-packaged Solutions: {comp['pre_packaged_count']} (expected: {comp['expected_pre_packaged_min']}+)")
        print(f"Individual Tests: {comp['individual_count']} (expected: {comp['expected_individual_min']}+)")
        
        print("\n" + "-"*70)
        print("2️⃣  DATA QUALITY EVALUATION")
        print("-"*70)
        qual = report['data_quality']
        print(f"Status: {qual['status']}")
        print(f"Score: {qual['score']:.2%}")
        print(f"Required Fields Complete: {qual['percentages']['required_complete']}")
        print(f"With Rich Description: {qual['percentages']['with_rich_description']}")
        print(f"With Job Levels: {qual['percentages']['with_job_levels']}")
        print(f"With Industries: {qual['percentages']['with_industries']}")
        print(f"With Languages: {qual['percentages']['with_languages']}")
        
        print("\n" + "-"*70)
        print("3️⃣  SAMPLE VALIDATION")
        print("-"*70)
        samp = report['sample_validation']
        print(f"Status: {samp['status']}")
        print(f"Sample Size: {samp['sample_size']}")
        print(f"All Required Fields Present: {samp['all_required_fields_present']}")
        print(f"Avg Metadata Completeness: {samp['average_metadata_completeness']:.2%}")
        
        print("\n" + "="*70)
        print(f"📅 Scrape Timestamp: {report['timestamp']}")
        print(f"📁 Source File: {report['source_file']}")
        print("="*70 + "\n")


def main():
    """Run scraping evaluation"""
    import sys
    
    data_path = "data/shl_products_complete.json"
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    
    evaluator = ScrapingEvaluator(data_path)
    evaluator.print_report()
    
    # Save report
    report = evaluator.generate_report()
    report_path = data_path.replace('.json', '_evaluation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Detailed report saved to: {report_path}\n")
    
    return report


if __name__ == "__main__":
    main()
