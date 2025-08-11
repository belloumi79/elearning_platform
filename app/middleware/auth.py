from functools import wraps
from flask import g, jsonify, request
import logging
from app.services.jwt_service import decode_token

logger = logging.getLogger(__name__)

def require_auth(f):
    """
    Decorator to protect routes that require authentication.
    It expects a JWT in the 'Authorization: Bearer <token>' header.
    If the token is valid, it attaches the user payload to flask.g.user.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({'error': 'Invalid Authorization header format. Expected "Bearer <token>"'}), 401

        token = parts[1]
        payload = decode_token(token)

        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid or expired access token'}), 401

        # Attach user payload to the request context
        g.user = payload
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """
    Decorator to protect routes that require admin privileges.
    Must be used *after* @require_auth.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.user should be set by the @require_auth decorator
        if not hasattr(g, 'user') or not g.user.get('isAdmin'):
            user_id = g.user.get('user_id', 'Unknown') if hasattr(g, 'user') else 'Unknown'
            logger.warning(f"Admin access denied for user {user_id}. User is not an admin.")
            return jsonify({'error': 'Admin access required.'}), 403 # 403 Forbidden

        logger.debug(f"Admin access granted for user {g.user.get('user_id')}")
        return f(*args, **kwargs)
    return decorated_function
