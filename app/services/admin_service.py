"""
Admin service module for the e-learning platform.

This module handles all admin-related database operations including
dashboard statistics, student management, course management, instructor management, and data retrieval.

Functions:
    get_dashboard_data_service: Retrieve dashboard statistics
    get_students_service: Get all students with their course information
    create_student_service: Create new student
    update_student_service: Update student information
    delete_student_service: Remove student from system
    get_courses_service: Get list of all courses
    create_course_service: Create a new course
    update_course_service: Update an existing course
    delete_course_service: Delete a course
    get_instructors_service: Get list of all instructors
    create_instructor_service: Create a new instructor
    delete_instructor_service: Delete an instructor
    get_course_by_id_service: Get a specific course by ID

Dependencies:
    - app.models.user: User model
    - app.models.course: Course model
    - app.models.student: Student model
    - app.models.instructor: Instructor model
    - app.database.supabase_db: Supabase database
"""

from app.models import User, Course, Student, Instructor
from app.database.supabase_db import get_supabase_client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_dashboard_data_service():
    """Get statistics and data for the admin dashboard."""
    try:
        supabase_client = get_supabase_client()

        # Get counts using supabase
        students_count_res = supabase_client.from_('students').select('*', count='exact').execute()
        courses_count_res = supabase_client.from_('courses').select('*', count='exact').execute()
        instructors_count_res = supabase_client.from_('instructors').select('*', count='exact').execute()

        total_students = students_count_res.count
        total_instructors = instructors_count_res.count

        # Get recent activities (last 5 items) using supabase
        recent_students_res = supabase_client.from_('students').select('*').order('created_at', desc=True).limit(5).execute()
        recent_courses_res = supabase_client.from_('courses').select('*').order('created_at', desc=True).limit(5).execute()

        recent_students = recent_students_res.data
        recent_courses = recent_courses_res.data

        return {
            'statistics': {
                'total_students': total_students,
                'total_courses': total_courses,
                'total_instructors': total_instructors
            },
            'recent_activities': {
                'students': recent_students,
                'courses': recent_courses
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise

def get_students_service():
    """Get list of all students with their course information."""
    try:
        supabase_client = get_supabase_client()
        students = []
        try:
            response = supabase_client.from_('students').select(
                '*, enrollments!inner(courses(id, title))'
            ).execute()

            if response.error:
                raise Exception(response.error.message)
            
            students_data = response.data
            
            for student_data in students_data:
                student = {
                    'id': student_data['id'],
                    'name': student_data['name'],
                    'email': student_data['email'],
                    'phone': student_data['phone'],
                    'status': student_data['status'],
                    'created_at': student_data['created_at'],
                }
                
                if student_data['enrollments'] and student_data['enrollments'][0]['courses']:
                    student['course'] = {
                        'id': student_data['enrollments'][0]['courses']['id'],
                        'title': student_data['enrollments'][0]['courses']['title']
                    }
                students.append(student)
            return students
        except Exception as e:
            logger.error(f"Error querying students from Supabase: {e}")
            raise
    except Exception as e:
        logger.error(f"Error in get_students_service: {e}")
        raise

def create_student_service(data):
    """Create a new student."""
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate course_id if provided
        course_id = data.get('course_id')
        course_data = None
        if course_id:
            try:
                supabase_client = get_supabase_client()
                response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
                if not response.data:
                    raise ValueError("Invalid course_id")
                course_data = response.data[0]
            except Exception as e:
                logger.error(f"Error validating course: {str(e)}")
                raise ValueError("Invalid course_id")

        # Create student document with transaction to ensure atomicity
        def create_student_in_transaction():
            supabase_client = get_supabase_client()
            student_data = {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }

            response_student = supabase_client.from_('students').insert(student_data).execute()
            if response_student.error:
                raise Exception(response_student.error.message)
            student_record = response_student.data[0]

            student_id = student_record['id']

            # If course_id is provided, create enrollment
            if course_id and course_data:
                enrollment_data = {
                    'student_id': student_id,
                    'course_id': course_id,
                    'enrolled_at': datetime.utcnow().isoformat(),
                    'status': 'active',
                    'course_title': course_data.get('title', 'Unknown Course')
                }
                response_enrollment = supabase_client.from_('enrollments').insert(enrollment_data).execute()
                if response_enrollment.error:
                    raise Exception(response_enrollment.error.message)

                # Add course information to student data
                student_data['course'] = {
                    'id': course_id,
                    'title': course_data.get('title', 'Unknown Course')
                }

            return student_id, student_data

        # Execute transaction
        student_id, student_data = create_student_in_transaction()
        
        # Return created student data
        created_student = student_data.copy()
        created_student['id'] = student_id
        return created_student

    except ValueError as e:
        logger.error(f"Validation error in create_student_service: {str(e)}")
        raise ValueError(f"Validation error creating student: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        raise RuntimeError(f"Failed to create student: {str(e)}")

def update_student_service(student_id, data):
    """Update a student's information."""
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        # Prepare update data
        update_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'updated_at': datetime.utcnow().isoformat()
        }

        # Update student record
        response = supabase_client.from_('students').update(update_data).eq('id', student_id).execute()
        if response.error:
            raise Exception(response.error.message)

        # Handle course enrollment if course_id is provided
        course_id = data.get('course_id')
        if course_id:
            # Verify course exists
            course_response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
            if not course_response.data:
                raise ValueError("Invalid course_id")
            
            # Check for existing enrollment
            enrollment_response = supabase_client.from_('enrollments') \
                .select('*') \
                .eq('student_id', student_id) \
                .eq('status', 'active') \
                .execute()
            
            if enrollment_response.data:
                # Update existing enrollment
                supabase_client.from_('enrollments') \
                    .update({
                        'course_id': course_id,
                        'updated_at': datetime.utcnow().isoformat()
                    }) \
                    .eq('id', enrollment_response.data[0]['id']) \
                    .execute()
            else:
                # Create new enrollment
                supabase_client.from_('enrollments').insert({
                    'student_id': student_id,
                    'course_id': course_id,
                    'enrolled_at': datetime.utcnow().isoformat(),
                    'status': 'active'
                }).execute()

        # Get updated student data
        student_response = supabase_client.from_('students').select('*').eq('id', student_id).execute()
        if not student_response.data:
            raise ValueError("Student not found after update")
            
        student_data = student_response.data[0]
        
        # Get course info if enrolled
        enrollment_response = supabase_client.from_('enrollments') \
            .select('*, courses!inner(title)') \
            .eq('student_id', student_id) \
            .eq('status', 'active') \
            .execute()
            
        if enrollment_response.data and enrollment_response.data[0]['courses']:
            student_data['course'] = {
                'id': enrollment_response.data[0]['course_id'],
                'title': enrollment_response.data[0]['courses']['title']
            }

        return student_data

    except ValueError as e:
        logger.error(f"Validation error in update_student_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        raise ValueError(f"Failed to update student: {str(e)}")

def delete_student_service(student_id):
    """Delete a student."""
    try:
        supabase_client = get_supabase_client()
        
        # First check if student exists
        response = supabase_client.from_('students').select('*').eq('id', student_id).execute()
        if not response.data:
            raise ValueError(f"Student with ID {student_id} not found")
            
        # Delete student
        delete_response = supabase_client.from_('students').delete().eq('id', student_id).execute()
        if delete_response.error:
            raise Exception(delete_response.error.message)
            
        # Also delete any enrollments
        supabase_client.from_('enrollments').delete().eq('student_id', student_id).execute()
        
    except ValueError as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise RuntimeError(f"Failed to delete student: {str(e)}")

def get_courses_service():
    """Get list of all courses."""
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.from_('courses').select('*').execute()
        if response.error:
            raise Exception(response.error.message)
        return response.data
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        raise RuntimeError(f"Failed to get courses: {str(e)}")

def create_course_service(data):
    """Create a new course."""
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'instructor_id', 'price']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate price is a number
        try:
            float(data['price'])
        except ValueError:
            raise ValueError("Price must be a number")

        supabase_client = get_supabase_client()
        
        # Prepare course data
        course_data = {
            'title': data['title'],
            'description': data['description'],
            'instructor_id': data['instructor_id'],
            'price': float(data['price']),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Create course
        response = supabase_client.from_('courses').insert(course_data).execute()
        if response.error:
            raise Exception(response.error.message)
            
        return response.data[0]

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
        response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
        if response.error:
            raise Exception(response.error.message)
        if not response.data:
            raise ValueError("Course not found")
        return response.data[0]
    except ValueError as e:
        logger.error(f"Course not found: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting course: {str(e)}")
        raise RuntimeError(f"Failed to get course: {str(e)}")
def update_course_service(course_id, data):
    """Update an existing course."""
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'instructor_id', 'price']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate price is a number
        try:
            float(data['price'])
        except ValueError:
            raise ValueError("Price must be a number")

        supabase_client = get_supabase_client()
        
        # Prepare update data
        update_data = {
            'title': data['title'],
            'description': data['description'],
            'instructor_id': data['instructor_id'],
            'price': float(data['price']),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Update course
        response = supabase_client.from_('courses').update(update_data).eq('id', course_id).execute()
        if response.error:
            raise Exception(response.error.message)
            
        # Get updated course data
        course_response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
        if not course_response.data:
            raise ValueError("Course not found after update")
            
        return course_response.data[0]

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
        
        # First check if course exists
        response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
        if not response.data:
            raise ValueError(f"Course with ID {course_id} not found")
            
        # Delete course
        delete_response = supabase_client.from_('courses').delete().eq('id', course_id).execute()
        if delete_response.error:
            raise Exception(delete_response.error.message)
            
    except ValueError as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise RuntimeError(f"Failed to delete course: {str(e)}")

def get_instructors_service():
    """Get list of all instructors."""
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.from_('instructors').select('*').execute()
        if response.error:
            raise Exception(response.error.message)
        return response.data
    except Exception as e:
        logger.error(f"Error getting instructors: {str(e)}")
        raise RuntimeError(f"Failed to get instructors: {str(e)}")

def create_instructor_service(data):
    """Create a new instructor."""
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        # Prepare instructor data
        instructor_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Create instructor
        response = supabase_client.from_('instructors').insert(instructor_data).execute()
        if response.error:
            raise Exception(response.error.message)
            
        # TODO: Handle password creation through auth service
        # This will need to be coordinated with the auth system
        
        return response.data[0]

    except ValueError as e:
        logger.error(f"Validation error in create_instructor_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating instructor: {str(e)}")
        raise RuntimeError(f"Failed to create instructor: {str(e)}")

def delete_instructor_service(email):
    """Delete an instructor by email."""
    try:
        supabase_client = get_supabase_client()
        
        # First check if instructor exists
        response = supabase_client.from_('instructors').select('*').eq('email', email).execute()
        if not response.data:
            raise ValueError(f"Instructor with email {email} not found")
            
        # Delete instructor
        delete_response = supabase_client.from_('instructors').delete().eq('email', email).execute()
        if delete_response.error:
            raise Exception(delete_response.error.message)
            
    except ValueError as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        raise RuntimeError(f"Failed to delete instructor: {str(e)}")
    """Update an existing course."""
