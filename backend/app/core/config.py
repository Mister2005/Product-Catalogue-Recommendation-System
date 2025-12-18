"""
Configuration management for the SHL Recommendation System
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_db_password: str = "postgres"  # Set this in .env
    database_url: str = ""  # Optional: direct PostgreSQL URL
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600
    
    # API Keys
    gemini_api_key: str = ""
    github_token: str = ""
    openai_api_key: str = ""
    
    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # RAG Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimension: int = 384
    top_k_results: int = 10
    
    # Recommendation Configuration
    default_recommendation_engine: str = "hybrid"
    max_recommendations: int = 10
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "SHL Assessment Recommendation Engine"
    version: str = "2.0.0"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Model Configuration
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
