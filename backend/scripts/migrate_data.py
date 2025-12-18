"""
Migration script to convert JSON data to PostgreSQL database
"""
import json
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.database import engine, Base, get_db
from app.models.database import Assessment, TestType, Industry, Language, Skill
from app.core.logging import log


def load_json_data(json_path: str) -> dict:
    """Load data from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def migrate_assessment(assessment_data: dict, db: Session):
    """Migrate single assessment to database"""
    # Check if assessment already exists
    existing = db.query(Assessment).filter(Assessment.id == assessment_data['id']).first()
    if existing:
        log.info(f"Assessment {assessment_data['id']} already exists, skipping")
        return
    
    # Create assessment
    assessment = Assessment(
        id=assessment_data['id'],
        name=assessment_data['name'],
        type=assessment_data['type'],
        remote_testing=assessment_data.get('remote_testing', False),
        adaptive=assessment_data.get('adaptive', False),
        job_family=assessment_data.get('job_family'),
        job_level=assessment_data.get('job_level'),
        description=assessment_data.get('description'),
        duration=assessment_data.get('duration')
    )
    
    db.add(assessment)
    db.flush()  # Flush to get the assessment ID
    
    # Add test types
    for test_type in assessment_data.get('test_types', []):
        tt = TestType(assessment_id=assessment.id, test_type=test_type)
        db.add(tt)
    
    # Add industries
    for industry in assessment_data.get('industries', []):
        ind = Industry(assessment_id=assessment.id, industry=industry)
        db.add(ind)
    
    # Add languages
    for language in assessment_data.get('languages', []):
        lang = Language(assessment_id=assessment.id, language=language)
        db.add(lang)
    
    # Add skills
    for skill in assessment_data.get('skills', []):
        sk = Skill(assessment_id=assessment.id, skill=skill)
        db.add(sk)
    
    log.info(f"Migrated assessment: {assessment.name}")


def migrate_all(json_path: str = "data/shl_products.json"):
    """Migrate all data from JSON to PostgreSQL"""
    log.info("Starting data migration from JSON to PostgreSQL")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created/verified")
    
    # Load JSON data
    json_path = Path(json_path)
    if not json_path.exists():
        log.error(f"JSON file not found: {json_path}")
        return
    
    data = load_json_data(json_path)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Migrate pre-packaged solutions
        pre_packaged = data.get('pre_packaged_solutions', [])
        log.info(f"Migrating {len(pre_packaged)} pre-packaged solutions")
        
        for assessment_data in pre_packaged:
            migrate_assessment(assessment_data, db)
        
        # Migrate individual test solutions
        individual = data.get('individual_test_solutions', [])
        log.info(f"Migrating {len(individual)} individual test solutions")
        
        for assessment_data in individual:
            migrate_assessment(assessment_data, db)
        
        # Commit all changes
        db.commit()
        log.info("Data migration completed successfully!")
        
        # Print statistics
        total_assessments = db.query(Assessment).count()
        total_test_types = db.query(TestType).count()
        total_industries = db.query(Industry).count()
        total_skills = db.query(Skill).count()
        
        log.info(f"Migration Statistics:")
        log.info(f"  - Assessments: {total_assessments}")
        log.info(f"  - Test Types: {total_test_types}")
        log.info(f"  - Industries: {total_industries}")
        log.info(f"  - Skills: {total_skills}")
        
    except Exception as e:
        log.error(f"Migration error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_all()
