"""
Database module for the e-learning platform, using Supabase PostgreSQL.

This module initializes and provides access to the Supabase client,
abstracting database interactions for the application.
"""

import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Use Service Role Key for backend database operations
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") 

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables for database module.")

# Initialize client with Service Role Key
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("Supabase client initialized with Service Role Key.")

def get_supabase_client():
    return supabase_client
