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

from flask import Blueprint, jsonify, request, current_app
import logging
from app.services.auth_service import supabase_admin_login, get_enhanced_user_data, signup_student
from app.services.jwt_service import create_access_token, create_refresh_token, decode_token

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login for both admins and students.
    Returns JWT access and refresh tokens upon successful authentication.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # The supabase_admin_login function can be used for any user login.
        # It returns user data, including an 'isAdmin' flag and enhanced user info.
        auth_response = supabase_admin_login(email, password)

        # Extract user data for the response
        user_info = auth_response.get('user', {})
        
        # Ensure email is properly set in user_info if it's missing
        if not user_info.get('email') and email:
            user_info['email'] = email
        
        # Prepare data for JWT payload
        jwt_payload = {
            'user_id': auth_response['uid'],
            'email': auth_response['email'],
            'isAdmin': auth_response.get('isAdmin', False),
            'role': user_info.get('role', 'user')
        }

        # Generate tokens
        access_token = create_access_token(data=jwt_payload)
        refresh_token = create_refresh_token(data=jwt_payload)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'user': user_info
        })

    except ValueError as e:
        # This can be raised from supabase_admin_login for invalid credentials
        logger.warning(f"Login failed for email {email}: {str(e)}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new student user with email and password.
    Returns JWT access and refresh tokens upon successful registration.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        phone = data.get('phone')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Register the student
        signup_response = signup_student(email, password, name, phone)

        # Prepare response data
        user_info = signup_response.get('user', {})

        return jsonify({
            'access_token': signup_response['access_token'],
            'refresh_token': signup_response['refresh_token'],
            'token_type': 'bearer',
            'user': user_info,
            'message': 'Student account created successfully'
        }), 201

    except ValueError as e:
        # This can be raised from signup_student for validation errors
        logger.warning(f"Signup failed for email {email}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred during signup: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refreshes an access token using a valid refresh token.
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400

        payload = decode_token(refresh_token)

        if not payload or payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid or expired refresh token'}), 401

        # Prepare new access token payload from the refresh token's payload
        new_access_token_payload = {
            'user_id': payload['user_id'],
            'email': payload['email'],
            'isAdmin': payload.get('isAdmin', False),
            'role': payload.get('role', 'user')
        }

        new_access_token = create_access_token(data=new_access_token_payload)
        
        # Get enhanced user data for consistency
        enhanced_user_data = get_enhanced_user_data(payload['user_id'])

        return jsonify({
            'access_token': new_access_token,
            'token_type': 'bearer',
            'user': enhanced_user_data
        })

    except Exception as e:
        logger.error(f"An unexpected error occurred during token refresh: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500


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
