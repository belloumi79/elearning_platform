"""
Authentication routes for the e-learning platform.

This module handles all authentication-related routes including
admin login, logout, and token verification.

Routes:
    - /admin/login: Admin login page
    - /api/admin/verify: Verify admin token and create session
    - /admin/logout: Clear admin session
    - /setup/admin/<email>: Create initial admin user (for setup only)
"""

from flask import Blueprint, jsonify, request, render_template, session, current_app
from firebase_admin import auth, firestore
import secrets
import logging
from datetime import datetime
from app.models.user import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login')
def admin_login():
    """Render admin login page."""
    return render_template('admin/login.html')

@auth_bp.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    """Verify Firebase ID token and create admin session.
    
    Request body must contain:
        - idToken: Firebase ID token
        
    Returns:
        JSON response with:
            - success: bool
            - error: str (if success is False)
    """
    try:
        # Get ID token from request
        id_token = request.json.get('idToken')
        if not id_token:
            raise ValueError("No ID token provided")
            
        # Verify token and admin status
        from app.services.auth_service import verify_admin_token
        user_data = verify_admin_token(id_token)
        
        # Create session
        session['user'] = user_data
        session['csrf_token'] = secrets.token_hex(32)
        
        return jsonify({
            'success': True,
            'csrfToken': session['csrf_token']
        })
        
    except Exception as e:
        logger.error(f"Admin verification failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

@auth_bp.route('/setup/admin/<email>')
def setup_admin(email):
    """Create initial admin user.
    This route should only be used once during initial setup.
    """
    try:
        logger.info(f"Setting up admin user for email: {email}")
        
        # Get user by email
        try:
            user = auth.get_user_by_email(email)
            logger.info(f"Found user: {user.uid}")
        except Exception as e:
            logger.error(f"Error finding user: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"User not found: {str(e)}"
            }), 404
        
        # Set admin custom claim
        try:
            auth.set_custom_user_claims(user.uid, {'admin': True})
            logger.info(f"Set admin claim for user: {user.uid}")
        except Exception as e:
            logger.error(f"Error setting admin claim: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Failed to set admin claim: {str(e)}"
            }), 500
        
        # Create admin document in Firestore
        try:
            db = firestore.client()
            admin_ref = db.collection('admins').document(user.uid)
            admin_ref.set({
                'email': email,
                'created_at': datetime.utcnow(),
                'uid': user.uid
            })
            logger.info(f"Created admin document for user: {user.uid}")
        except Exception as e:
            logger.error(f"Error creating admin document: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Failed to create admin document: {str(e)}"
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Successfully set up admin user: {email}',
            'uid': user.uid
        })
    except Exception as e:
        logger.error(f"Failed to set up admin user: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/logout')
def admin_logout():
    """Clear the admin session."""
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/user/profile/<uid>', methods=['GET'])
def get_user_profile_route(uid):
    """
    Get user profile and enrolled courses.

    Args:
        uid (str): User ID

    Returns:
        JSON response with user profile and enrolled courses
    """
    try:
        from app.services.auth_service import get_user_profile
        user_profile = get_user_profile(uid)
        return jsonify(user_profile)
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
