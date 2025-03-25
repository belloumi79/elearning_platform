"""Database package for the e-learning platform."""

from app.database.supabase_db import get_supabase_client

__all__ = ['get_supabase_client']
