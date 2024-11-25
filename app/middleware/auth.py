from functools import wraps
from flask import session, jsonify, request
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug("Checking authentication")
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("No Authorization header found")
            return jsonify({'error': 'No token provided'}), 401
            
        try:
            id_token = auth_header.split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
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
