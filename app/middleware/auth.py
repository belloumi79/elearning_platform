from functools import wraps
from flask import session, jsonify, request
import logging
from supabase import create_client, Client
from postgrest.exceptions import APIError # Import APIError
import os

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables.")

# Initialize Supabase client once at module level
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("Auth Middleware initialized with Supabase client.")

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log entry point and requested path
        logger.debug(f"Entering require_auth decorator for path: {request.path}")

        if 'user' not in session:
            logger.warning(f"Authentication failed for path {request.path}: No user session found")
            return jsonify({'error': 'Authentication required. No active session.'}), 401

        access_token = session.get('access_token')
        refresh_token = session.get('refresh_token') # Needed for refresh attempt

        if not access_token:
            logger.warning("Authentication failed: Access token not found in session.")
            # Don't clear session here, let the user try again or handle on frontend
            return jsonify({'error': 'Invalid session state. Please log in again.'}), 401

        try:
            # 1. Try to get user with current access token
            logger.debug("Attempting to validate access token with Supabase.")
            user_response = supabase.auth.get_user(access_token)

            # 2. Check for errors (including expired token)
            if user_response.user is None or hasattr(user_response, 'error') and user_response.error:
                error_message = "Authentication error"
                is_expired = False
                if hasattr(user_response, 'error') and user_response.error:
                    error_message = str(user_response.error)
                    # Check if the error indicates an expired token
                    if "token expired" in error_message.lower() or "jwt expired" in error_message.lower():
                         is_expired = True
                         logger.info("Access token expired. Attempting refresh.")
                    else:
                         logger.warning(f"Access token validation failed: {error_message}")
                else:
                    logger.warning("Access token validation failed: No user returned and no explicit error.")

                # 3. If expired and refresh token exists, attempt refresh
                if is_expired and refresh_token:
                    try:
                        logger.info("Attempting token refresh using refresh_token.")
                        refresh_response = supabase.auth.refresh_session(refresh_token)

                        if refresh_response.session:
                            logger.info("Token refresh successful.")
                            # Update session with new tokens
                            session['access_token'] = refresh_response.session.access_token
                            if hasattr(refresh_response.session, 'refresh_token') and refresh_response.session.refresh_token:
                                session['refresh_token'] = refresh_response.session.refresh_token
                            # Update user info in session as well (keep isAdmin status from old session for now)
                            session['user'] = {'id': refresh_response.user.id, 'isAdmin': session['user'].get('isAdmin', False)}
                            session.modified = True # Mark session as modified
                            user_response = refresh_response # Use the refreshed response
                        else:
                            logger.warning(f"Token refresh failed. Response: {refresh_response}")
                            session.clear()
                            return jsonify({'error': 'Session expired. Please log in again.'}), 401

                    except Exception as refresh_err:
                        logger.error(f"Exception during token refresh: {str(refresh_err)}")
                        session.clear()
                        return jsonify({'error': 'Session refresh failed. Please log in again.'}), 401
                else:
                    # Token is invalid (not expired) or no refresh token available
                    logger.warning("Token invalid or refresh token missing. Clearing session.")
                    session.clear()
                    return jsonify({'error': 'Invalid session or token. Please log in again.'}), 401

            # 4. If token is valid (or was refreshed), get user ID
            current_user = user_response.user
            user_id = current_user.id
            logger.debug(f"Token validated/refreshed for user ID: {user_id}. Proceeding with DB checks.")
            logger.debug(f"Current session state before DB checks: {session}")

            # 5. Verify user exists in a relevant local table IF NOT ADMIN
            is_admin_from_session = session.get('user', {}).get('isAdmin', False)
            
            # Skip all DB checks if user is admin in session
            if is_admin_from_session:
                logger.debug(f"User {user_id} is admin in session. Skipping all DB checks.")
            else:
                logger.debug(f"User {user_id} is not admin in session. Proceeding with DB checks.")
                
                # 6. Attach user info to request context (optional)
                # request.user = {'id': user_id, 'email': current_user.email}

                # 7. Verify admin status against 'admins' table (only for non-admins)
                logger.debug(f"Step 7: Verifying admin status for user {user_id} in 'admins' table.")
                is_admin_from_db = False
                admin_check_successful = False
                try:
                    admin_response = supabase.from_('admins').select('user_id', count='exact').eq('user_id', user_id).execute()
                    logger.debug(f"Admin check DB raw response object: {admin_response}")
                    db_count = getattr(admin_response, 'count', None)
                    logger.debug(f"Admin check DB response count: {db_count}")

                    if db_count is not None and db_count > 0:
                        is_admin_from_db = True
                        logger.debug(f"User {user_id} confirmed as admin via DB check.")
                    else:
                        logger.debug(f"User {user_id} confirmed as NOT admin via DB check.")
                    admin_check_successful = True
                except Exception as admin_check_err:
                    logger.error(f"Database error during admin status check for {user_id}: {admin_check_err}", exc_info=True)
                    is_admin_from_db = is_admin_from_session

                # Update session if DB check was successful and status differs
                if admin_check_successful and is_admin_from_session != is_admin_from_db:
                    logger.warning(f"Admin status mismatch for user {user_id} (Session: {is_admin_from_session}, DB: {is_admin_from_db}). Updating session.")
                    session['user']['isAdmin'] = is_admin_from_db
                    session.modified = True

            # Final check for the require_admin decorator downstream
            # Note: The require_admin decorator itself provides the primary enforcement based on session['user']['isAdmin']

            logger.debug(f"Authentication check successful for user {user_id}. Final isAdmin status in session: {session['user']['isAdmin']}")
            return f(*args, **kwargs) # Proceed to the protected route

        except Exception as e:
            # Catch-all for unexpected errors during the process
            logger.error(f"Unexpected error during authentication check: {str(e)}", exc_info=True)
            return jsonify({'error': 'An internal error occurred during authentication.'}), 500

    return decorated_function

# --- require_admin remains the same ---

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug("Checking admin authorization via require_admin decorator")

        # Check session existence first
        if 'user' not in session:
            logger.warning("Admin access denied - no user session found")
            return jsonify({'error': 'Admin access required. No active session.'}), 403 # Use 403 Forbidden

        # Check isAdmin flag within the session
        if not session['user'].get('isAdmin'):
            user_id = session['user'].get('id', 'Unknown')
            logger.warning(f"Admin access denied for user {user_id} - isAdmin flag is false or missing in session.")
            return jsonify({'error': 'Admin access required.'}), 403 # Use 403 Forbidden

        logger.debug(f"Admin access granted for user {session['user'].get('id')}")
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
