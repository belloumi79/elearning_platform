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
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and Anon key must be set in environment variables.")

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_client():
    return supabase_client
