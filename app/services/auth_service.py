"""
Authentication service module for the e-learning platform.

This module handles Firebase token verification and admin status checking.
It interacts with Firebase Authentication and Firestore to validate user
credentials and retrieve user data.

Functions:
    verify_admin_token: Verify Firebase ID token and check admin status

Dependencies:
    - firebase_admin.auth: For token verification
    - firebase_admin.firestore: For user data retrieval
"""

from firebase_admin import auth, firestore
import logging
from app.models.user import User
from datetime import datetime
from app.models.student import Student
from app.models.course import Course

logger = logging.getLogger(__name__)
db = firestore.client()

def verify_admin_token(id_token):
    try:
        logger.info("Starting token verification process...")
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        logger.info(f"Token verified successfully. Claims: {decoded_token.get('claims', {})}")

        uid = decoded_token['uid']
        
        # Check if user is admin before adding to 'users' collection
        is_admin = False
        try:
            admin_ref = db.collection('admins').document(uid)
            admin_doc = admin_ref.get()
            is_admin = admin_doc.exists
        except Exception as e:
            logger.error(f"Error checking admin status in Firestore: {str(e)}")

        # Add user to 'users' collection if not admin
        if not is_admin:
            try:
                user_ref = db.collection('users').document(uid)
                user_data = {
                    'uid': uid,
                    'email': decoded_token['email'],
                    'created_at': datetime.utcnow()
                }
                user_ref.set(user_data, merge=True)
                logger.info(f"User {uid} added/updated in Firestore")
            except Exception as e:
                logger.error(f"Error adding/updating user in Firestore: {str(e)}")

        # First check if user exists in admins collection
        try:
            admin_ref = db.collection('admins').document(uid)
            admin_doc = admin_ref.get()

            if admin_doc.exists:
                logger.info(f"User {uid} verified as admin through admins collection")
                # Set admin claim for future use (important!)
                #auth.set_custom_user_claims(uid, {"admin": True})  # May not be necessary
                # You can fetch additional admin info if needed
                admin_data = admin_doc.to_dict()
                user_info = {**admin_data, 'isAdmin': True}  # Merge admin data and isAdmin flag

                # You might want to fetch the user's name from auth
                #user = auth.get_user(uid)
                #user_info['name'] = user.display_name
            else:
                logger.warning(f"User {uid} not found in admins collection")
                raise ValueError("User is not authorized as admin")

        except Exception as e:
            logger.error(f"Error checking admin status in Firestore: {str(e)}")
            raise  # Re-raise the exception after logging

        return user_info  # Return user info if successful


    except auth.InvalidIdTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise


def create_admin_user(email):
    """
    Create or verify an admin user in Firestore.
    This should be run once to set up the initial admin.
    """
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Set admin custom claim
        auth.set_custom_user_claims(user.uid, {'admin': True})
        
        # Create admin document in Firestore
        admin_ref = db.collection('admins').document(user.uid)
        admin_ref.set({
            'email': email,
            'created_at': datetime.utcnow(),
            'uid': user.uid
        })
        
        logger.info(f"Successfully created admin user for {email}")
        return True
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
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
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            logger.warning(f"User {uid} not found in users collection")
            raise ValueError("User not found")

        user_data = user_doc.to_dict()
        user = User.from_dict(user_data)
        user_profile = user.to_dict()

        # Check if user is a student
        student_ref = db.collection('students').document(uid)
        student_doc = student_ref.get()
        if student_doc.exists:
            student_data = student_doc.to_dict()
            student = Student.from_dict(student_data)
            user_profile['student'] = student.to_dict()
        else:
            user_profile['student'] = None

        # Fetch enrolled courses
        enrollments_ref = db.collection('enrollments').where('student_id', '==', uid)
        enrollments = enrollments_ref.get()
        enrolled_courses = []
        for enrollment in enrollments:
            course_id = enrollment.to_dict().get('course_id')
            if course_id:
                course_ref = db.collection('courses').document(course_id)
                course_doc = course_ref.get()
                if course_doc.exists:
                    course_data = course_doc.to_dict()
                    course = Course.from_dict(course_data)
                    enrolled_courses.append(course.to_dict())
        user_profile['enrolled_courses'] = enrolled_courses
        return user_profile

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise
