from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, HttpUrl, Field

class HealthCheck(BaseModel):
    status: str

class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None

class AssessmentItem(BaseModel):
    url: str
    name: str 
    adaptive_support: str = Field(..., description="Yes/No indicating adaptive testing support")
    description: str
    duration: int = Field(..., description="Duration in minutes")
    remote_support: str = Field(..., description="Yes/No indicating remote testing support")
    test_type: List[str] = Field(..., description="Categories or types of the assessment")

class RecommendationResponse(BaseModel):
    recommended_assessments: List[AssessmentItem]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str
    context: Optional[Any] = None
