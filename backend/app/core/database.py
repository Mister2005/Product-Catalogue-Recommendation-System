"""
Database connection and session management - Pure Supabase Client
"""
from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()

# Stub Base class for backward compatibility with existing models
# (not used with Supabase, but prevents import errors)
class Base:
    """Stub base class for compatibility"""
    pass

# Supabase client (singleton)
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client
    
    Returns:
        Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and API key must be set in environment variables")
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client


def get_db() -> Client:
    """
    Dependency to get Supabase client
    
    Returns:
        Supabase client
    """
    return get_supabase_client()
