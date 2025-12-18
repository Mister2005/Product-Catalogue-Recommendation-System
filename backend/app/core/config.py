"""
Configuration management for the SHL Recommendation System
"""
import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_db_password: str = ""
    database_url: str = ""  # Optional: direct PostgreSQL URL
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600
    
    # API Keys
    gemini_api_key: str = ""
    github_token: str = ""
    openai_api_key: str = ""
    
    # Application Configuration
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        # In production, ensure we have valid origins
        if self.is_production and not origins:
            raise ValueError("ALLOWED_ORIGINS must be set in production")
        return origins
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
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
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    
    def validate_production_settings(self) -> None:
        """Validate that required settings are configured for production"""
        if not self.is_production:
            return
        
        errors = []
        
        if not self.supabase_url:
            errors.append("SUPABASE_URL is required")
        if not self.supabase_key:
            errors.append("SUPABASE_KEY is required")
        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required")
        if self.secret_key == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed for production")
        if self.debug:
            errors.append("DEBUG should be False in production")
        
        if errors:
            raise ValueError(f"Production configuration errors: {', '.join(errors)}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Validate production settings on startup
    if settings.is_production:
        settings.validate_production_settings()
    
    return settings
