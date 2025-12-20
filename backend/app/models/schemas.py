"""
Pydantic schemas for API requests and responses
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime
from uuid import UUID


class TestTypeEnum(str, Enum):
    """Assessment test types"""
    COGNITIVE = "C"
    PERSONALITY = "P"
    ABILITY = "A"
    BEHAVIORAL = "B"
    KNOWLEDGE = "K"
    SIMULATION = "S"
    EMOTIONAL_INTELLIGENCE = "E"
    DEVELOPMENT = "D"


class JobLevelEnum(str, Enum):
    """Organizational job levels"""
    ENTRY = "Entry Level"
    INTERMEDIATE = "Intermediate"
    SENIOR = "Senior"
    EXECUTIVE = "Executive"
    MANAGER = "Manager"
    SUPERVISOR = "Supervisor"


class RecommendationEngineEnum(str, Enum):
    """Available recommendation engines"""
    GEMINI = "gemini"
    NLP = "nlp"
    CLUSTERING = "clustering"
    RAG = "rag"
    HYBRID = "hybrid"


# Request Schemas

# NEW SIMPLIFIED SCHEMAS (SHL Assignment)
class RecommendRequest(BaseModel):
    """Simplified request for recommendations - accepts query or URL"""
    query: Optional[str] = Field(None, description="Natural language query or job description text")
    url: Optional[str] = Field(None, description="URL containing job description")
    
    def model_post_init(self, __context):
        """Validate that at least one of query or url is provided"""
        if not self.query and not self.url:
            raise ValueError('Either query or url must be provided')


# OLD COMPLEX SCHEMA (Deprecated - keeping for backward compatibility)
class RecommendationRequest(BaseModel):
    """Request model for recommendations (DEPRECATED - use RecommendRequest)"""
    model_config = ConfigDict(use_enum_values=True)
    
    job_title: Optional[str] = Field(None, description="Target job title")
    job_family: Optional[str] = Field(None, description="Job family category")
    job_level: Optional[JobLevelEnum] = Field(None, description="Target job level")
    industry: Optional[str] = Field(None, description="Industry sector")
    required_skills: Optional[List[str]] = Field(default_factory=list, description="Required skills")
    test_types: Optional[List[TestTypeEnum]] = Field(default_factory=list, description="Preferred test types")
    remote_testing_required: bool = Field(False, description="Remote testing requirement")
    max_duration: Optional[int] = Field(None, description="Maximum duration in minutes")
    language: Optional[str] = Field("English", description="Preferred language")
    num_recommendations: int = Field(5, ge=1, le=20, description="Number of recommendations")
    engine: RecommendationEngineEnum = Field(RecommendationEngineEnum.HYBRID, description="Recommendation engine")
    user_id: Optional[str] = Field(None, description="User identifier for tracking")


class AssessmentCreate(BaseModel):
    """Schema for creating assessments"""
    id: str
    name: str
    type: str
    test_types: List[str] = []
    remote_testing: bool = False
    adaptive: bool = False
    job_family: Optional[str] = None
    job_level: Optional[str] = None
    industries: List[str] = []
    languages: List[str] = []
    skills: List[str] = []
    description: Optional[str] = None
    duration: Optional[int] = None


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    recommendation_id: UUID
    assessment_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None


# Response Schemas

# NEW SIMPLIFIED SCHEMAS (SHL Assignment)
class AssessmentRecommendation(BaseModel):
    """Single assessment recommendation - simplified format"""
    assessment_name: str
    assessment_url: str


class RecommendResponse(BaseModel):
    """Simplified recommendation response"""
    recommendations: List[AssessmentRecommendation]


# OLD COMPLEX SCHEMAS (Deprecated - keeping for backward compatibility)
class AssessmentResponse(BaseModel):
    """Response model for assessment (DEPRECATED)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    type: str
    test_types: List[str]
    remote_testing: bool
    adaptive: bool
    job_family: Optional[str]
    job_level: Optional[str]
    industries: List[str]
    languages: List[str]
    skills: List[str]
    description: Optional[str]
    duration: Optional[int]


class RecommendationScore(BaseModel):
    """Score breakdown for a recommendation"""
    total_score: float
    relevance_score: float
    skill_match_score: Optional[float] = None
    industry_match_score: Optional[float] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None


class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    assessment: AssessmentResponse
    score: RecommendationScore
    rank: int


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[RecommendationItem]
    total_count: int
    engine_used: str
    query_summary: str
    metadata: Optional[Dict[str, Any]] = None
    recommendation_id: Optional[UUID] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    database: str
    cache: str


class MetadataResponse(BaseModel):
    """Metadata response"""
    job_families: List[str]
    industries: List[str]
    skills: List[str]
    test_types: List[str]
    job_levels: List[str]
    languages: List[str]


class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request"""
    message: str = Field(..., description="User message")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(..., description="AI response")
    context: Optional[str] = Field(None, description="Additional context used")
