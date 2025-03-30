"""
Authentication service module for the e-learning platform.

This module handles Supabase authentication and admin status checking.
It interacts with Supabase Auth and Supabase Postgres to validate user
credentials and retrieve user data.
"""

import logging
from app.models.user import User
from datetime import datetime
from app.models.student import Student
from app.models.course import Course
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)

# Initialize Supabase client using Service Role Key for backend operations
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables for auth service.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("AuthService initialized with Supabase client using Service Role Key.")


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
        # 1. Sign in using Supabase Auth
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # Check for Supabase Auth errors explicitly if possible (depends on library version)
        # Assuming response object contains user info on success
        if response.user:
            user = response.user
            uid = user.id
            logger.info(f"Supabase Auth successful for user ID: {uid}")

            # 2. Verify if the user is listed in the 'admins' table using the correct column 'user_id'
            try:
                logger.info(f"Checking 'admins' table for user_id: {uid}") # Log the UID being checked
                # Use the global 'supabase' client, not 'self.supabase'
                admin_check_response = supabase.from_('admins').select("user_id").eq('user_id', uid).limit(1).execute() 
                
                logger.info(f"Admin check response data: {admin_check_response.data}") # Log the response data
                logger.debug(f"Full admin check response: {admin_check_response}") # Log the full response for debugging

                if admin_check_response.data:
                    logger.info(f"User {uid} confirmed as admin.")
                    # Return necessary user info for session
                    return {
                        'uid': uid,
                        'email': user.email,
                        'isAdmin': True 
                    }
                else:
                    logger.warning(f"User {uid} authenticated but is not an admin.")
                    # Sign out the user as they are not authorized for the admin panel
                    supabase.auth.sign_out() 
                    raise ValueError("User is not authorized as admin.")
            except Exception as db_error:
                logger.error(f"Error checking admin status in Supabase table 'admins': {str(db_error)}")
                # Sign out the user due to uncertainty
                supabase.auth.sign_out()
                raise Exception("Failed to verify admin status.")
        else:
            # Handle cases where sign_in_with_password might not raise an error but returns no user
            # (Check Supabase client library documentation for exact error handling)
            logger.warning(f"Supabase Auth failed for email: {email}. Response might indicate error.")
            # Attempt to extract error message if available
            error_message = "Invalid email or password." # Default message
            if hasattr(response, 'error') and response.error:
                 error_message = response.error.message
            elif hasattr(response, 'message'): # Some versions might use 'message'
                 error_message = response.message
            raise ValueError(error_message)

    except Exception as e:
        # Catch specific Supabase exceptions if the library defines them, otherwise catch general Exception
        logger.error(f"Supabase admin login error for {email}: {str(e)}")
        # Re-raise ValueErrors for credential issues, wrap others
        if isinstance(e, ValueError):
            raise e
        else:
            # Log the original error but raise a generic one
            raise Exception(f"An unexpected error occurred during login: {str(e)}")


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
        user = User.from_dict(user_data)
        user_profile = user.to_dict()

        # Check if user is a student
        response = supabase.from_('students').select("*").eq('student_id', uid).execute()
        if response.data:
            student_data_list = response.data
            if student_data_list:
                student_data = student_data_list[0]
                student = Student.from_dict(student_data)
                user_profile['student'] = student.to_dict()
            else:
                user_profile['student'] = None # Student data not found, but user might still be a student record
        else:
            user_profile['student'] = None

        # Fetch enrolled courses
        response = supabase.from_('enrollments').select("*").eq('student_id', uid).execute()
        enrollments_data = response.data
        enrolled_courses = []
        if enrollments_data:
            for enrollment_data in enrollments_data:
                course_id = enrollment_data.get('course_id')
                if course_id:
                    course_response = supabase.from_('courses').select("*").eq('course_id', course_id).execute()
                    course_data_list = course_response.data
                    if course_data_list:
                        course_data = course_data_list[0]
                        course = Course.from_dict(course_data)
                        enrolled_courses.append(course.to_dict())
        user_profile['enrolled_courses'] = enrolled_courses
        return user_profile

    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise
