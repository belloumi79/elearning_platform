"""
Courses Service
---------------
This service handles the business logic for course-related operations.
"""
import logging
from datetime import datetime
from app.database.supabase_db import get_supabase_client

logger = logging.getLogger(__name__)

def get_courses_service():
    """Get list of all courses."""
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.from_('courses').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        raise RuntimeError(f"Failed to get courses: {str(e)}")

def create_course_service(data):
    """Create a new course."""
    try:
        required_fields = ['title', 'instructor_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()

        try:
            instructor_check = supabase_client.from_('instructors').select('id').eq('id', data['instructor_id']).maybe_single().execute()
            if not instructor_check.data:
                 raise ValueError(f"Instructor with ID {data['instructor_id']} not found.")
        except Exception as ie:
             logger.error(f"Error checking instructor ID {data['instructor_id']}: {str(ie)}")
             raise ValueError(f"Failed to verify instructor ID: {str(ie)}")

        course_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'instructor_id': data['instructor_id'],
            'price': data.get('price', 0.0),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        supabase_client.from_('courses').insert(course_data).execute()
        return course_data
    except ValueError as e:
        logger.error(f"Validation error in create_course_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise RuntimeError(f"Failed to create course: {str(e)}")

def get_course_by_id_service(course_id):
    """Get a specific course by ID."""
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.from_('courses').select('*').eq('id', course_id).maybe_single().execute()
        if not response.data:
            return None
        return response.data
    except Exception as e:
        logger.error(f"Error getting course: {str(e)}")
        raise RuntimeError(f"Failed to get course: {str(e)}")

def update_course_service(course_id, data):
    """Update an existing course."""
    try:
        required_fields = ['title', 'instructor_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        update_data = {
            'title': data['title'],
            'description': data.get('description'),
            'instructor_id': data['instructor_id'],
            'price': data.get('price'),
            'updated_at': datetime.utcnow().isoformat()
        }
        # Filter out None values so we only update provided fields
        update_data = {k: v for k, v in update_data.items() if v is not None}

        supabase_client.from_('courses').update(update_data).eq('id', course_id).execute()

        course_response = supabase_client.from_('courses').select('*').eq('id', course_id).maybe_single().execute()
        if not course_response.data:
            raise ValueError("Course not found after update")
            
        return course_response.data
    except ValueError as e:
        logger.error(f"Validation error in update_course_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating course: {str(e)}")
        raise RuntimeError(f"Failed to update course: {str(e)}")

def delete_course_service(course_id):
    """Delete a course."""
    try:
        supabase_client = get_supabase_client()
        
        response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
        if not response.data:
            raise ValueError(f"Course with ID {course_id} not found")
            
        supabase_client.from_('courses').delete().eq('id', course_id).execute()
        
    except ValueError as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise RuntimeError(f"Failed to delete course: {str(e)}")
