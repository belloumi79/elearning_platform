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

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and Anon key must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def verify_admin_token(access_token):
    try:
        logger.info("Starting token verification process...")
        user = supabase.auth.get_user(access_token)
        if user.error:
            logger.error(f"Token verification failed: {user.error}")
            raise ValueError(f"Invalid token: {user.error}")

        logger.info(f"Token verified successfully. User ID: {user.user.id}")
        uid = user.user.id

        # Check if user is admin
        is_admin = False
        try:
            response = supabase.from_('admins').select("*").eq('uid', uid).execute()
            if response.data:
                is_admin = True
        except Exception as e:
            logger.error(f"Error checking admin status in Supabase: {str(e)}")

        # Add user to 'users' table if not exists (or update)
        try:
            response = supabase.from_('users').select("*").eq('uid', uid).execute()
            if not response.data:
                user_data = {
                    'uid': uid,
                    'email': user.user.email,
                    'created_at': datetime.utcnow().isoformat()  # Use ISO format for datetime
                }
                response = supabase.from_('users').insert(user_data).execute()
                logger.info(f"User {uid} added to Supabase users table")
            else:
                logger.info(f"User {uid} already exists in Supabase users table")
        except Exception as e:
            logger.error(f"Error adding/updating user in Supabase: {str(e)}")

        if is_admin:
            logger.info(f"User {uid} verified as admin")
            user_info = {'uid': uid, 'email': user.user.email, 'isAdmin': True}
            return user_info
        else:
            logger.warning(f"User {uid} not authorized as admin")
            raise ValueError("User is not authorized as admin")

    except ValueError as ve:
        raise ve  # Re-raise ValueError
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise


def create_admin_user(email):
    """
    Create or verify an admin user in Supabase 'admins' table.
    This should be run once to set up the initial admin.
    """
    try:
        # Find user by email in auth.users table
        response = supabase.auth.admin.list_users(emails=[email])
        if response.users:
            user = response.users[0]
            uid = user.id

            # Insert admin record in 'admins' table
            admin_data = {
                'uid': uid,
                'email': email,
                'created_at': datetime.utcnow().isoformat()
            }
            response = supabase.from_('admins').insert(admin_data).execute()
            if response.error:
                logger.error(f"Error creating admin user in Supabase: {response.error}")
                raise Exception(f"Supabase error: {response.error.message}")

            logger.info(f"Successfully created admin user for {email}")
            return True
        else:
            logger.error(f"User with email {email} not found in Supabase Auth")
            raise ValueError(f"User with email {email} not found in Supabase Auth")

    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise


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
