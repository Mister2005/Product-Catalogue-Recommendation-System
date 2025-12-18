"""
Database models for assessments and recommendations
"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, 
    ForeignKey, TIMESTAMP, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Assessment(Base):
    """Assessment model"""
    __tablename__ = "assessments"
    
    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    remote_testing = Column(Boolean, default=False, index=True)
    adaptive = Column(Boolean, default=False)
    job_family = Column(String(200), index=True)
    job_level = Column(String(100), index=True)
    description = Column(Text)
    duration = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    embedding = Column(ARRAY(Float))  # Vector embedding for RAG
    
    # Relationships
    test_types = relationship("TestType", back_populates="assessment", cascade="all, delete-orphan")
    industries = relationship("Industry", back_populates="assessment", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="assessment", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="assessment", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="assessment", cascade="all, delete-orphan")


class TestType(Base):
    """Test type model (many-to-many with Assessment)"""
    __tablename__ = "test_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(255), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    test_type = Column(String(50), nullable=False)
    
    assessment = relationship("Assessment", back_populates="test_types")


class Industry(Base):
    """Industry model"""
    __tablename__ = "industries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(255), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    industry = Column(String(200), nullable=False)
    
    assessment = relationship("Assessment", back_populates="industries")


class Language(Base):
    """Language model"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(255), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(100), nullable=False)
    
    assessment = relationship("Assessment", back_populates="languages")


class Skill(Base):
    """Skill model"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(255), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    skill = Column(String(200), nullable=False)
    
    assessment = relationship("Assessment", back_populates="skills")


class RecommendationHistory(Base):
    """Recommendation history model"""
    __tablename__ = "recommendation_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), index=True)
    query_text = Column(Text, nullable=False)
    query_parameters = Column(JSON)
    recommended_assessments = Column(JSON, nullable=False)
    recommendation_engine = Column(String(50), nullable=False)
    scores = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    # Relationships
    feedbacks = relationship("UserFeedback", back_populates="recommendation", cascade="all, delete-orphan")


class UserFeedback(Base):
    """User feedback model"""
    __tablename__ = "user_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendation_history.id", ondelete="CASCADE"))
    assessment_id = Column(String(255), ForeignKey("assessments.id", ondelete="CASCADE"))
    rating = Column(Integer)  # 1-5
    feedback_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    recommendation = relationship("RecommendationHistory", back_populates="feedbacks")
    assessment = relationship("Assessment", back_populates="feedbacks")
