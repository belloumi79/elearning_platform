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
                    # Get enhanced user data
                    enhanced_user_data = get_enhanced_user_data(uid, user.email)
                    # Return necessary user info for session
                    return {
                        'uid': uid,
                        'email': user.email,
                        'isAdmin': True,
                        'access_token': response.session.access_token,
                        'refresh_token': response.session.refresh_token,
                        'user': enhanced_user_data
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


def get_enhanced_user_data(user_id: str, email: str = ""):
    """
    Retrieve comprehensive user data from all relevant tables.
    
    Args:
        user_id (str): Supabase Auth user ID
        email (str): User's email (optional, can be passed from authenticated user)
        
    Returns:
        dict: Enhanced user data with profile information
    """
    try:
        logger.info(f"Fetching enhanced user data for user_id: {user_id}")
        
        # Initialize user data with defaults
        user_data = {
            'id': user_id,
            'email': email or '',  # Use the passed email parameter
            'name': '',
            'firstName': '',
            'lastName': '',
            'phone': '',
            'isAdmin': False,
            'status': 'active',
            'role': 'user',
            'created_at': None,
            'last_sign_in_at': None,
            'profile_type': 'unknown',
            'profile_id': None
        }
        
        # Check admin profile
        try:
            admin_response = supabase.from_('admins').select("*").eq('user_id', user_id).execute()
            if admin_response.data and len(admin_response.data) > 0:
                admin_record = admin_response.data[0]
                user_data.update({
                    'name': admin_record.get('email', '').split('@')[0],  # Fallback name from email
                    'isAdmin': True,
                    'role': 'admin',
                    'profile_type': 'admin',
                    'profile_id': admin_record['id'],
                    'status': admin_record.get('status', 'active'),
                    'created_at': admin_record.get('created_at'),
                    'updated_at': admin_record.get('updated_at')
                })
                logger.info(f"Found admin profile for user {user_id}")
        except Exception as admin_error:
            logger.warning(f"Error fetching admin profile: {str(admin_error)}")
        
        # Check student profile (only if not already found as admin)
        if not user_data['isAdmin']:
            try:
                student_response = supabase.from_('students').select("*").eq('user_id', user_id).execute()
                if student_response.data and len(student_response.data) > 0:
                    student_record = student_response.data[0]
                    user_data.update({
                        'name': student_record.get('name', ''),
                        'phone': student_record.get('phone', ''),
                        'isAdmin': False,
                        'role': 'student',
                        'profile_type': 'student',
                        'profile_id': student_record['id'],
                        'status': student_record.get('status', 'active'),
                        'created_at': student_record.get('created_at'),
                        'updated_at': student_record.get('updated_at')
                    })
                    logger.info(f"Found student profile for user {user_id}")
            except Exception as student_error:
                logger.warning(f"Error fetching student profile: {str(student_error)}")
        
        # Check instructor profile (only if not already found as admin or student)
        if user_data['profile_type'] == 'unknown':
            try:
                instructor_response = supabase.from_('instructors').select("*").eq('user_id', user_id).execute()
                if instructor_response.data and len(instructor_response.data) > 0:
                    instructor_record = instructor_response.data[0]
                    user_data.update({
                        'name': instructor_record.get('name', ''),
                        'phone': instructor_record.get('phone', ''),
                        'isAdmin': False,
                        'role': 'instructor',
                        'profile_type': 'instructor',
                        'profile_id': instructor_record['id'],
                        'status': instructor_record.get('status', 'active'),
                        'created_at': instructor_record.get('created_at'),
                        'updated_at': instructor_record.get('updated_at')
                    })
                    logger.info(f"Found instructor profile for user {user_id}")
            except Exception as instructor_error:
                logger.warning(f"Error fetching instructor profile: {str(instructor_error)}")
        
        # Parse name into first and last name if available
        if user_data.get('name'):
            name_parts = user_data['name'].split()
            if len(name_parts) >= 2:
                user_data['firstName'] = ' '.join(name_parts[:-1])
                user_data['lastName'] = name_parts[-1]
            else:
                user_data['firstName'] = user_data['name']
                user_data['lastName'] = ''
        
        logger.info(f"Successfully fetched enhanced user data for user {user_id}")
        return user_data
        
    except Exception as e:
        logger.error(f"Error fetching enhanced user data: {str(e)}", exc_info=True)
        # Return basic user data as fallback
        return {
            'id': user_id,
            'email': 'unknown@example.com',
            'name': '',
            'firstName': '',
            'lastName': '',
            'phone': '',
            'isAdmin': False,
            'status': 'active',
            'role': 'user',
            'created_at': None,
            'last_sign_in_at': None,
            'profile_type': 'unknown',
            'profile_id': None
        }


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
def adapt_user_json_to_database(user_json):
    """
    Adapt user JSON object to database structure.

    Args:
        user_json (dict): User JSON object from auth response

    Returns:
        dict: Database adaptation info with table name and data
    """
    try:
        logger.info(f"Adapting user JSON for profile_type: {user_json.get('profile_type')}")

        profile_type = user_json.get('profile_type')
        profile_id = user_json.get('profile_id')
        user_id = user_json.get('id')
        email = user_json.get('email')
        created_at = user_json.get('created_at')

        if profile_type == 'admin':
            # Adapt for admins table
            admin_data = {
                'id': profile_id,
                'user_id': user_id,
                'email': email,
                'created_at': created_at,
                'updated_at': datetime.utcnow().isoformat()
            }
            return {
                'table': 'admins',
                'data': admin_data,
                'operation': 'upsert'  # Insert or update on conflict
            }
        elif profile_type == 'student':
            # Adapt for students table
            student_data = {
                'id': profile_id,
                'user_id': user_id,
                'name': user_json.get('name', ''),
                'email': email,
                'phone': user_json.get('phone'),
                'status': user_json.get('status', 'active'),
                'created_at': created_at,
                'updated_at': datetime.utcnow().isoformat()
            }
            return {
                'table': 'students',
                'data': student_data,
                'operation': 'upsert'
            }
        elif profile_type == 'instructor':
            # Adapt for instructors table
            instructor_data = {
                'id': profile_id,
                'user_id': user_id,
                'name': user_json.get('name', ''),
                'email': email,
                'phone': user_json.get('phone'),
                'status': user_json.get('status', 'active'),
                'created_at': created_at,
                'updated_at': datetime.utcnow().isoformat()
            }
            return {
                'table': 'instructors',
                'data': instructor_data,
                'operation': 'upsert'
            }
        else:
            logger.warning(f"Unknown profile_type: {profile_type}")
            return None

    except Exception as e:
        logger.error(f"Error adapting user JSON: {str(e)}")
        raise
        raise
