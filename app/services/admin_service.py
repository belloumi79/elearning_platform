"""
Admin service module for the e-learning platform.

This module handles all admin-related database operations including
dashboard statistics, student management, and instructor management.

Functions:
    get_dashboard_data_service: Retrieve dashboard statistics
    get_students_service: Get all students with their course information
    create_student_service: Create new student
    update_student_service: Update student information
    delete_student_service: Remove student from system
    get_instructors_service: Get list of all instructors
    create_instructor_service: Create a new instructor
    delete_instructor_service: Delete an instructor
"""

from app.database.supabase_db import get_supabase_client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_dashboard_data_service():
    """Get statistics and data for the admin dashboard."""
    try:
        supabase_client = get_supabase_client() # Uses Service Key now

        # Get counts using supabase - select only 'id' for counting
        students_count_res = supabase_client.from_('students').select('id', count='exact').execute()
        courses_count_res = supabase_client.from_('courses').select('id', count='exact').execute()
        instructors_count_res = supabase_client.from_('instructors').select('id', count='exact').execute()

        # Safely access count attribute
        total_students = students_count_res.count if hasattr(students_count_res, 'count') else 0
        total_courses = courses_count_res.count if hasattr(courses_count_res, 'count') else 0
        total_instructors = instructors_count_res.count if hasattr(instructors_count_res, 'count') else 0


        # Get recent activities (last 5 items) using supabase
        recent_students_res = supabase_client.from_('students').select('*').order('created_at', desc=True).limit(5).execute()
        recent_courses_res = supabase_client.from_('courses').select('*').order('created_at', desc=True).limit(5).execute()

        # Safely access data attribute
        recent_students = recent_students_res.data if recent_students_res.data else []
        recent_courses = recent_courses_res.data if recent_courses_res.data else []

        # Fetch recent registrations (enrollments) with error handling
        try:
            recent_registrations_res = supabase_client.from_('enrollments').select(
                'id, created_at, student:students(id, name, email), course:courses(id, title)'
            ).order('created_at', desc=True).limit(5).execute()

            recent_registrations = recent_registrations_res.data if recent_registrations_res.data else []
        except Exception as enroll_err:
            logger.error(f"Error fetching recent registrations: {str(enroll_err)}")
            recent_registrations = []

        return {
            'statistics': {
                'total_students': total_students,
                'total_courses': total_courses,
                'total_instructors': total_instructors
            },
            'recent_activities': {
                'students': recent_students,
                'courses': recent_courses
            },
            'recent_registrations': recent_registrations
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
            # Use LEFT join to include students without enrollments
            # Select specific columns for clarity and potentially better performance
            response = supabase_client.from_('students').select(
                'id, name, email, phone, status, created_at, enrollments!left(id, courses!inner(id, title))'
            ).execute()

            if response.data is None:
                 logger.warning("Supabase query for students returned None data.")
                 if hasattr(response, 'error') and response.error:
                      raise Exception(f"Supabase error: {response.error.message}")
                 return []

            students_data = response.data
            
            for student_data in students_data:
                student = {
                    'id': student_data['id'],
                    'name': student_data['name'],
                    'email': student_data['email'],
                    'phone': student_data['phone'],
                    'status': student_data['status'],
                    'created_at': student_data.get('created_at'),
                }
                
                enrollments = student_data.get('enrollments', [])
                if enrollments:
                    first_enrollment = enrollments[0]
                    course_data = first_enrollment.get('courses')
                    if course_data:
                         student['course'] = {
                             'id': course_data.get('id'),
                             'title': course_data.get('title')
                         }
                    else:
                         student['course'] = None
                else:
                    student['course'] = None

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
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        student_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        insert_response = supabase_client.from_('students').insert(student_data).execute()

        if hasattr(insert_response, 'error') and insert_response.error:
             logger.error(f"Supabase error during student insert: {insert_response.error.message}")
             raise Exception(f"Failed to insert student record: {insert_response.error.message}")
        if not insert_response.data:
             logger.error(f"Student insert seemed successful but no data returned. Response: {insert_response}")
             raise Exception("Failed to retrieve student data after creation (no data in insert response).")

        if not isinstance(insert_response.data, list) or not insert_response.data:
             logger.error(f"Unexpected data format in insert response: {insert_response.data}")
             raise Exception("Unexpected response format after student insert.")

        created_student_partial = insert_response.data[0]
        created_student_id = created_student_partial.get('id')
        if not created_student_id:
             logger.error(f"Could not find 'id' in insert response data: {created_student_partial}")
             raise Exception("Could not determine created student ID.")

        select_response = supabase_client.from_('students').select('*').eq('id', created_student_id).single().execute()

        if hasattr(select_response, 'error') and select_response.error:
             logger.error(f"Supabase error selecting student after insert: {select_response.error.message}")
             raise Exception(f"Failed to select student record after creation: {select_response.error.message}")
        if not select_response.data:
             logger.error(f"Could not select student record (ID: {created_student_id}) after successful insert.")
             raise Exception("Failed to retrieve full student record after creation.")

        created_student = select_response.data
        
        if 'course_id' in data:
            try:
                course_response = supabase_client.from_('courses').select('title').eq('id', data['course_id']).execute()
                if not course_response.data:
                    raise ValueError("Invalid course_id")
                    
                course_title = course_response.data[0].get('title', 'Unknown Course')
                
                enrollment_data = {
                    'student_id': created_student['id'],
                    'course_id': data['course_id'],
                    'enrolled_at': datetime.utcnow().isoformat(),
                    'status': 'active',
                    'course_title': course_title
                }
                
                enrollment_response = supabase_client.from_('enrollments').insert(enrollment_data).execute()
                if enrollment_response.error:
                    raise Exception(enrollment_response.error.message)
                    
                created_student['course'] = {
                    'id': data['course_id'],
                    'title': course_title
                }
                
            except Exception as e:
                logger.warning(f"Course enrollment failed but student created: {str(e)}")

        return created_student

    except ValueError as e:
        logger.error(f"Validation error in create_student_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        raise RuntimeError(f"Failed to create student: {str(e)}")

def update_student_service(student_id, data):
    """Update a student's information."""
    try:
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        update_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'updated_at': datetime.utcnow().isoformat()
        }

        response = supabase_client.from_('students').update(update_data).eq('id', student_id).execute()
        if response.error:
            raise Exception(response.error.message)

        course_id = data.get('course_id')
        if course_id:
            course_response = supabase_client.from_('courses').select('*').eq('id', course_id).execute()
            if not course_response.data:
                raise ValueError("Invalid course_id")
            
            enrollment_response = supabase_client.from_('enrollments') \
                .select('*') \
                .eq('student_id', student_id) \
                .eq('status', 'active') \
                .execute()
            
            if enrollment_response.data:
                supabase_client.from_('enrollments') \
                    .update({
                        'course_id': course_id,
                        'updated_at': datetime.utcnow().isoformat()
                    }) \
                    .eq('id', enrollment_response.data[0]['id']) \
                    .execute()
            else:
                supabase_client.from_('enrollments').insert({
                    'student_id': student_id,
                    'course_id': course_id,
                    'enrolled_at': datetime.utcnow().isoformat(),
                    'status': 'active'
                }).execute()

        student_response = supabase_client.from_('students').select('*').eq('id', student_id).execute()
        if not student_response.data:
            raise ValueError("Student not found after update")
            
        student_data = student_response.data[0]
        
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
        
        response = supabase_client.from_('students').select('*').eq('id', student_id).execute()
        if not response.data:
            raise ValueError(f"Student with ID {student_id} not found")
            
        delete_response = supabase_client.from_('students').delete().eq('id', student_id).execute()
        if delete_response.error:
            raise Exception(delete_response.error.message)
            
        supabase_client.from_('enrollments').delete().eq('student_id', student_id).execute()
        
    except ValueError as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise RuntimeError(f"Failed to delete student: {str(e)}")

def get_instructors_service():
    """Get list of all instructors."""
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.from_('instructors').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting instructors: {str(e)}")
        raise RuntimeError(f"Failed to get instructors: {str(e)}")

def create_instructor_service(data):
    """Create a new instructor."""
    try:
        required_fields = ['name', 'email', 'phone', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()
        
        try:
            existing = supabase_client.from_('instructors').select('email').eq('email', data['email']).execute()
            if existing.data and len(existing.data) > 0:
                raise ValueError(f"L'email {data['email']} existe déjà")

            auth_response = supabase_client.auth.sign_up({
                "email": data['email'],
                "password": data['password'],
                "options": {
                    "data": {
                        'name': data['name'],
                        'role': 'instructor'
                    }
                }
            })
            
            if not auth_response.user:
                logger.error(f"Auth user creation failed: {auth_response}")
                raise Exception("Failed to create auth user")
                
            user_id = auth_response.user.id
            
        except Exception as auth_err:
            logger.error(f"Error creating auth user for instructor: {str(auth_err)}")
            raise RuntimeError(f"Failed to create auth user: {str(auth_err)}")

        try:
            instructor_data = {
                'id': user_id,
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone']
            }
            
            response = supabase_client.from_('instructors').insert(instructor_data).execute()
            
            if not response.data:
                logger.error(f"Instructor record insert failed: {response}")
                raise Exception("Failed to insert instructor record")
                
            return response.data[0]
            
        except Exception as db_err:
            logger.error(f"Error creating instructor DB record: {str(db_err)}")
            supabase_client.auth.admin.delete_user(user_id)
            raise RuntimeError(f"Failed to create instructor record: {str(db_err)}")

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
        
        response = supabase_client.from_('instructors').select('id').eq('email', email).execute()
        if not response.data:
            raise ValueError(f"Instructor with email {email} not found")
            
        instructor_id = response.data[0]['id']
        
        supabase_client.from_('instructors').delete().eq('id', instructor_id).execute()
        
        supabase_client.auth.admin.delete_user(instructor_id)
        
    except ValueError as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        raise RuntimeError(f"Failed to delete instructor: {str(e)}")
