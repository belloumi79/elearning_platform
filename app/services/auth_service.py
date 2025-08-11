"""
Authentication service module for the e-learning platform.

This module handles Supabase authentication and admin status checking.
It interacts with Supabase Auth and Supabase Postgres to validate user
credentials and retrieve user data.
"""

import logging
from datetime import datetime
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)

# Initialize Supabase client using Service Role Key for backend operations
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    logger.critical("SUPABASE_URL environment variable is not set for auth service.")
    raise ValueError("Supabase URL must be set in environment variables for auth service.")
if not SUPABASE_SERVICE_KEY:
    logger.critical("SUPABASE_SERVICE_ROLE_KEY environment variable is not set for auth service.")
    raise ValueError("Supabase Service Role Key must be set in environment variables for auth service.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("AuthService initialized with Supabase client using Service Role Key.")
except Exception as e:
    logger.critical(f"Failed to initialize Supabase client in auth service: {str(e)}", exc_info=True)
    raise RuntimeError("Critical: Supabase client failed to initialize in auth service.") from e

def update_user_password(user_id: str, new_password: str):
    """
    Updates a user's password using Supabase's admin API.
    
    Args:
        user_id (str): The ID of the user whose password needs to be updated.
        new_password (str): The new password for the user.
        
    Raises:
        Exception: If the password update fails.
    """
    try:
        logger.info(f"Attempting to update password for user ID: {user_id}")
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        if response.user:
            logger.info(f"Password updated successfully for user ID: {user_id}")
            return True
        else:
            error_message = "Unknown error during password update."
            if hasattr(response, 'error') and response.error:
                error_message = response.error.message
            logger.error(f"Failed to update password for user ID {user_id}: {error_message}")
            raise Exception(f"Failed to update password: {error_message}")
    except Exception as e:
        logger.error(f"Error updating password for user ID {user_id}: {str(e)}")
        raise Exception(f"Error updating password: {str(e)}")


def supabase_admin_login(email, password):
    """
    Authenticates a user with email/password using Supabase Auth
    and verifies if they are an admin by checking the 'admins' table.

    Args:
        email (str): User's email.
        password (str): User's password.

    Returns:
        dict: User information relevant for the session if login is successful
              and the user is an admin. Includes 'uid', 'email', 'isAdmin'.

    Raises:
        ValueError: If authentication fails or the user is not an admin.
        Exception: For other Supabase or unexpected errors.
    """
    try:
        logger.info(f"Attempting Supabase login for email: {email}")
        # Create a public client for login (using anon key)
        SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
        if not SUPABASE_ANON_KEY:
            raise ValueError("Supabase ANON_KEY must be set in environment variables")
        
        public_supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # 1. Sign in using public client
        response = public_supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # Check for Supabase Auth errors
        if response.user:
            user = response.user
            uid = user.id
            logger.info(f"Supabase Auth successful for user ID: {uid}")

            # 2. Verify if the user is listed in the 'admins' table using the service client
            try:
                logger.info(f"Checking 'admins' table for user_id: {uid}")
                admin_check_response = supabase.from_('admins').select("user_id").eq('user_id', uid).execute()
                
                if admin_check_response.data and len(admin_check_response.data) > 0:
                    logger.info(f"User {uid} confirmed as admin.")
                    # Return necessary user info for session
                    return {
                        'uid': uid,
                        'email': user.email,
                        'isAdmin': True,
                        'access_token': response.session.access_token,
                        'refresh_token': response.session.refresh_token
                    }
                else:
                    logger.warning(f"User {uid} authenticated but is not an admin.")
                    # Sign out the user as they are not authorized for the admin panel
                    public_supabase.auth.sign_out()
                    raise ValueError("User is not authorized as admin.")
            except Exception as db_error:
                logger.error(f"Error checking admin status: {str(db_error)}")
                public_supabase.auth.sign_out()
                raise Exception("Failed to verify admin status.")
        else:
            # Handle sign-in failure
            error_message = "Invalid email or password."
            if hasattr(response, 'error') and response.error:
                 error_message = response.error.message
            elif hasattr(response, 'message'):
                 error_message = response.message
            raise ValueError(error_message)

    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        if isinstance(e, ValueError):
            raise e
        else:
            raise Exception(f"An unexpected error occurred: {str(e)}")


# Removed verify_admin_token function as it's replaced by supabase_admin_login


# Removed create_admin_user function as the route was removed


def signup_with_gmail(access_token):
    """Sign up a new user with Gmail using Supabase access token.

    Args:
        access_token (str): Supabase access token

    Returns:
        str: User ID

    Raises:
        ValueError: If no access token is provided or if the token is invalid.
    """
    try:
        # Get user from access token
        user = supabase.auth.get_user(access_token)
        if user.error:
            logger.error(f"Invalid token: {user.error}")
            raise ValueError(f"Invalid token: {user.error}")

        uid = user.user.id
        email = user.user.email

        # Check if the user already exists in 'users' table
        response = supabase.from_('users').select("*").eq('uid', uid).execute()
        if response.data:
            logger.info(f"User {uid} already exists")
            return uid

        # Create a new user in 'users' table
        user_data = {
            'uid': uid,
            'email': email,
            'created_at': datetime.utcnow().isoformat()
        }
        response = supabase.from_('users').insert(user_data).execute()
        if response.error:
            logger.error(f"Error signing up user: {response.error}")
            raise Exception(f"Supabase error: {response.error.message}")

        logger.info(f"User {uid} created successfully")
        return uid

    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error signing up user: {str(e)}")
        raise


def get_user_profile(uid):
    """
    Get user profile and enrolled courses.

    Args:
        uid (str): User ID

    Returns:
        dict: User profile and enrolled courses
    """
    try:
        logger.info(f"Fetching user profile for UID: {uid}")
        # Fetch user from 'users' table
        response = supabase.from_('users').select("*").eq('uid', uid).execute()
        if not response.data:
            logger.warning(f"User {uid} not found in users table")
            raise ValueError("User not found")

        user_data_list = response.data
        if not user_data_list:
            raise ValueError("No user data found")
        user_data = user_data_list[0] # Assuming only one user with given uid
        user_profile = user_data

        # Check if user is a student
        response = supabase.from_('students').select("*").eq('user_id', uid).execute()
        if response.data:
            user_profile['student'] = response.data[0]
        else:
            user_profile['student'] = None

        # Fetch enrolled courses
        response = supabase.from_('enrollments').select('*, courses(*)').eq('student_id', uid).execute()
        user_profile['enrolled_courses'] = [item['courses'] for item in response.data if item.get('courses')]
        
        return user_profile

    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise
