"""
Student Service
---------------
This service handles business logic for student-related operations.
"""
import logging
from app.database.supabase_db import get_supabase_client
from datetime import datetime

logger = logging.getLogger(__name__)

def get_student_profile(student_id: str):
    """
    Retrieves a student's profile from the database.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.from_('students').select('*').eq('id', student_id).single().execute()
        
        if not response.data:
            return None
            
        return response.data
    except Exception as e:
        logger.error(f"Error fetching profile for student {student_id}: {str(e)}", exc_info=True)
        raise

def update_student_profile(student_id: str, data: dict):
    """
    Updates a student's profile in the database.
    Only allows updating 'name' and 'phone' for security.
    """
    try:
        # Validate that only allowed fields are being updated
        allowed_fields = {'name', 'phone'}
        update_data = {key: value for key, value in data.items() if key in allowed_fields}

        if not update_data:
            raise ValueError("No valid fields to update. Only 'name' and 'phone' are allowed.")

        supabase = get_supabase_client()
        response = supabase.from_('students').update(update_data).eq('id', student_id).execute()

        # After update, fetch the updated record to return it
        if response.data:
            updated_profile_response = supabase.from_('students').select('*').eq('id', student_id).single().execute()
            return updated_profile_response.data
        else:
            # This case might indicate the student_id didn't exist
            raise ValueError("Student not found or update failed.")

    except ValueError as ve:
        logger.warning(f"Validation error updating profile for student {student_id}: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error updating profile for student {student_id}: {str(e)}", exc_info=True)
        raise

def enroll_student_in_course(student_id: str, course_id: str):
    """
    Enrolls a student in a specific course.
    """
    try:
        supabase = get_supabase_client()

        # 1. Check if the course exists
        course_res = supabase.from_('courses').select('id').eq('id', course_id).maybe_single().execute()
        if not course_res.data:
            raise ValueError("Course not found.")

        # 2. Check if the student is already enrolled
        enrollment_res = supabase.from_('enrollments').select('id').eq('student_id', student_id).eq('course_id', course_id).execute()
        if enrollment_res.data:
            raise ValueError("Student is already enrolled in this course.")

        # 3. Create the new enrollment
        enrollment_data = {
            'student_id': student_id,
            'course_id': course_id,
            'enrolled_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        new_enrollment_res = supabase.from_('enrollments').insert(enrollment_data).execute()

        return new_enrollment_res.data[0] if new_enrollment_res.data else None

    except ValueError as ve:
        raise
    except Exception as e:
        logger.error(f"Database error enrolling student {student_id} in course {course_id}: {str(e)}", exc_info=True)
        raise

def get_student_courses(student_id: str):
    """
    Retrieves a list of all courses a student is enrolled in.
    """
    try:
        supabase = get_supabase_client()
        # Select courses by joining through the enrollments table
        response = supabase.from_('enrollments').select('courses(*)').eq('student_id', student_id).execute()
        
        # The result will be a list of {'courses': {...}} objects. We extract the course details.
        courses = [item['courses'] for item in response.data if item.get('courses')]
        
        return courses
    except Exception as e:
        logger.error(f"Error fetching courses for student {student_id}: {str(e)}", exc_info=True)
        raise