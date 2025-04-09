"""
Authentication routes for the e-learning platform.

This module handles all authentication-related routes including
admin login, logout, and token verification.

Routes:
    - /admin/login: Admin login page
    - /admin/login: Admin login page (renders template)
    - /api/admin/login: Handle admin login using email/password (Supabase)
    - /admin/logout: Clear admin session
    # - /setup/admin/<email>: Create initial admin user (Firebase - REMOVED)
    # - /api/signup: User signup (Firebase - REMOVED)
    # - /api/user/profile/<uid>: Get user profile (Firebase - NEEDS REFACTOR)
"""

from flask import Blueprint, jsonify, request, render_template, session, current_app
# Removed Firebase imports: from firebase_admin import auth, firestore
# Initialize Supabase client directly
import os
from supabase import create_client, Client
import secrets
import logging
from datetime import datetime
# Removed: from app.models.user import User # Assuming User model might change or be unused with Supabase auth

logger = logging.getLogger(__name__)

# Initialize Supabase client (similar to auth_service.py and middleware/auth.py)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Use service key if needed for admin actions, otherwise ANON_KEY

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    # Use ANON_KEY as fallback if service key isn't strictly needed for login check
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("Supabase URL and Anon or Service key must be set in environment variables.")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    logger.warning("Using Supabase Anon Key for auth routes. Service Key might be required for admin operations.")
else:
    # Prefer service key if available, might be needed later
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Using Supabase Service Key for auth routes.")


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login')
def admin_login():
    """Render admin login page."""
    return render_template('admin/login.html')

@auth_bp.route('/api/admin/login', methods=['POST']) # Renamed from /verify
def api_admin_login():
    """Handle admin login using email/password with Supabase."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise ValueError("Email and password are required")

        # Call Supabase login function (to be implemented in auth_service)
        # This service function should also verify if the user is an admin
        from app.services.auth_service import supabase_admin_login
        user_data = supabase_admin_login(email, password) # This needs to return necessary user info for session

        # Create session
        session['user'] = {'id': user_data['uid'], 'isAdmin': user_data['isAdmin']} # Store relevant Supabase user info (e.g., id, isAdmin)
        session['csrf_token'] = secrets.token_hex(32) # Keep CSRF token for form protection
        session['access_token'] = user_data['access_token']
        session['refresh_token'] = user_data['refresh_token']

        # Return success and the access token
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'csrfToken': session['csrf_token'] # Optional: only if frontend needs it explicitly
        })

    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}")
        # Provide slightly more specific error messages based on the exception type
        error_message = 'An unexpected error occurred during login.'
        status_code = 500
        if isinstance(e, ValueError):
            # Specific messages from auth_service for credential/admin issues
            error_message = str(e)
            status_code = 401 # Unauthorized or Forbidden (depending on exact meaning)
        elif "Invalid email or password" in str(e): # Catch potential generic Supabase auth error string
             error_message = "Invalid email or password."
             status_code = 401
        # Keep logging the detailed error server-side
        # logger.error(f"Admin login failed: {str(e)}") # Already logged in auth_service

        return jsonify({
            'success': False,
            'error': error_message
        }), status_code


# @auth_bp.route('/setup/admin/<email>') # Firebase specific - Removed
# def setup_admin(email):
#     """Create initial admin user. (Firebase version - REMOVED)"""
#     # ... (Firebase code removed) ...
#     pass


@auth_bp.route('/admin/logout')
def admin_logout():
    """Clear the admin session."""
    session.clear()
    # Redirect to login page after logout might be better UX
    # from flask import redirect, url_for
    # return jsonify({'success': True, 'message': 'Logged out successfully'})


# @auth_bp.route('/api/signup', methods=['POST']) # Firebase specific - Removed
# def signup():
#     """Sign up a new user. (Firebase version - REMOVED)"""
#     # ... (Firebase code removed) ...
#     pass


# @auth_bp.route('/api/user/profile/<uid>', methods=['GET']) # Needs refactoring for Supabase
# def get_user_profile_route(uid):
#     """Get user profile. (Needs refactoring for Supabase)"""
#     # try:
#     #     from app.services.auth_service import get_user_profile_supabase
#     #     user_profile = get_user_profile_supabase(uid)
#     #     return jsonify(user_profile)
#     # except Exception as e:
#     #     logger.error(f"Error fetching user profile: {str(e)}")
#     #     return jsonify({
#     #         'success': False,
#     #         'error': str(e)
#     #     }), 500
#     return jsonify({"message": "Route needs refactoring for Supabase"}), 501
