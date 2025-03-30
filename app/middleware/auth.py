from functools import wraps
from flask import session, jsonify, request
import logging
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and Anon key must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug("Checking authentication")
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logger.warning("No Authorization header found")
            return jsonify({'error': 'No token provided'}), 401

        try:
            access_token = auth_header.split('Bearer ')[1]
            user = supabase.auth.get_user(access_token)
            if user.error:
                logger.error(f"Authentication error: {user.error}")
                return jsonify({'error': 'Authentication failed'}), 401
            request.user = user.user
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug("Checking admin authorization")

        if 'user' not in session or not session['user'].get('isAdmin'):
            logger.warning("Admin access denied - no admin session")
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function

def verify_csrf_token():
    csrf_token = request.form.get('csrf_token')
    if not csrf_token:
        csrf_token = request.headers.get('X-CSRF-TOKEN')

    stored_token = session.get('csrf_token')

    if not csrf_token or not stored_token or csrf_token != stored_token:
        logger.warning("CSRF token verification failed")
        return False
    return True
