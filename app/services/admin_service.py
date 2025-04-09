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

            # Proper error check for Supabase v2+ (assuming execute raises on HTTP error)
            # No explicit 'response.error' check needed here usually, but check data
            if response.data is None:
                 # This might indicate an issue, log it. Actual errors should raise exceptions.
                 logger.warning("Supabase query for students returned None data.")
                 # Handle potential errors if the library doesn't raise them
                 if hasattr(response, 'error') and response.error:
                      raise Exception(f"Supabase error: {response.error.message}")
                 # If no error but None data, return empty list
                 return []

            students_data = response.data
            
            for student_data in students_data:
                student = {
                    'id': student_data['id'],
                    'name': student_data['name'],
                    'email': student_data['email'],
                    'phone': student_data['phone'],
                    'status': student_data['status'],
                    'created_at': student_data.get('created_at'), # Use .get for safety
                }
                
                # Safely access nested data
                enrollments = student_data.get('enrollments', [])
                if enrollments:
                    # Check if the first enrollment has a course linked (inner join on courses means it should if enrollment exists)
                    first_enrollment = enrollments[0]
                    course_data = first_enrollment.get('courses')
                    if course_data:
                         student['course'] = {
                             'id': course_data.get('id'),
                             'title': course_data.get('title')
                         }
                    else:
                         student['course'] = None # No course linked to the first enrollment found
                else:
                    student['course'] = None # No enrollments found for the student

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

        supabase_client = get_supabase_client()
        
        # Prepare student data
        student_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Step 1: Insert student data
        insert_response = supabase_client.from_('students').insert(student_data).execute()

        # Check for errors after insert execution
        # Check if error attribute exists and is truthy
        if hasattr(insert_response, 'error') and insert_response.error:
             logger.error(f"Supabase error during student insert: {insert_response.error.message}")
             raise Exception(f"Failed to insert student record: {insert_response.error.message}")
        if not insert_response.data:
             logger.error(f"Student insert seemed successful but no data returned. Response: {insert_response}")
             raise Exception("Failed to retrieve student data after creation (no data in insert response).")

        # Get the ID from the insert response data
        if not isinstance(insert_response.data, list) or not insert_response.data:
             logger.error(f"Unexpected data format in insert response: {insert_response.data}")
             raise Exception("Unexpected response format after student insert.")

        created_student_partial = insert_response.data[0]
        created_student_id = created_student_partial.get('id')
        if not created_student_id:
             logger.error(f"Could not find 'id' in insert response data: {created_student_partial}")
             raise Exception("Could not determine created student ID.")

        # Step 2: Select the full student record using the ID to ensure we have all fields
        logger.debug(f"Selecting newly created student with ID: {created_student_id}")
        select_response = supabase_client.from_('students').select('*').eq('id', created_student_id).single().execute()

        # Check for errors after select execution
        if hasattr(select_response, 'error') and select_response.error:
             logger.error(f"Supabase error selecting student after insert: {select_response.error.message}")
             # Consider if we need to rollback the insert here? Difficult without transactions.
             raise Exception(f"Failed to select student record after creation: {select_response.error.message}")
        if not select_response.data:
             logger.error(f"Could not select student record (ID: {created_student_id}) after successful insert.")
             raise Exception("Failed to retrieve full student record after creation.")

        created_student = select_response.data # .single() returns the dict directly
        
        # Handle course enrollment if provided
        if 'course_id' in data:
            try:
                # Verify course exists
                course_response = supabase_client.from_('courses').select('title').eq('id', data['course_id']).execute()
                if not course_response.data:
                    raise ValueError("Invalid course_id")
                    
                course_title = course_response.data[0].get('title', 'Unknown Course')
                
                # Create enrollment
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
                    
                # Add course info to student response
                created_student['course'] = {
                    'id': data['course_id'],
                    'title': course_title
                }
                
            except Exception as e:
                logger.warning(f"Course enrollment failed but student created: {str(e)}")
                # Student was created successfully even if enrollment failed

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
        # Execute the query. If there's an HTTP error, execute() should raise it.
        response = supabase_client.from_('courses').select('*').execute()
        # No need to check response.error explicitly in newer versions
        return response.data
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        raise RuntimeError(f"Failed to get courses: {str(e)}")

def create_course_service(data):
    """Create a new course."""
    try:
        # Validation for title and instructor_id (description/price handled in route)
        required_fields = ['title', 'instructor_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        supabase_client = get_supabase_client()

        # Verify instructor_id exists before proceeding
        try:
            instructor_check = supabase_client.from_('instructors').select('id').eq('id', data['instructor_id']).maybe_single().execute()
            if not instructor_check.data:
                 raise ValueError(f"Instructor with ID {data['instructor_id']} not found.")
        except Exception as ie:
             # Catch potential errors during the check itself
             logger.error(f"Error checking instructor ID {data['instructor_id']}: {str(ie)}")
             raise ValueError(f"Failed to verify instructor ID: {str(ie)}")


        # Prepare course data
        course_data = {
            'title': data['title'],
            'description': data.get('description', ''), # Use validated/defaulted value
            'instructor_id': data['instructor_id'],
            'price': data['price'], # Use validated/defaulted float value
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Create course
        # Execute the insert. If there's an HTTP error, execute() should raise it.
        supabase_client.from_('courses').insert(course_data).execute()

        # If execute() did not raise an error, assume success.
        # Return the data that was intended for insertion.
        # Note: This won't include the database-generated 'id'.
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
        # Use maybe_single() to fetch zero or one record directly
        response = supabase_client.from_('courses').select('*').eq('id', course_id).maybe_single().execute()
        # execute() will raise an exception on HTTP error in newer clients
        if not response.data:
            raise ValueError("Course not found")
        return response.data # maybe_single() returns the dict directly, or None
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
        required_fields = ['title', 'instructor_id', 'type']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate type
        if data['type'] not in ['free', 'paid']:
            raise ValueError("Invalid course type - must be 'free' or 'paid'")

        # Validate price based on type
        if data['type'] == 'paid':
            if 'price' not in data:
                raise ValueError("Price is required for paid courses")
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
        # Execute the update. If there's an HTTP error, execute() should raise it.
        supabase_client.from_('courses').update(update_data).eq('id', course_id).execute()
        # No need to check response.error explicitly

        # Get updated course data with all fields including type
        course_response = supabase_client.from_('courses').select('*').eq('id', course_id).maybe_single().execute()
        if not course_response.data:
            raise ValueError("Course not found after update")

        # Ensure type field is included, default to 'paid' if missing for backward compatibility
        course_data = course_response.data
        if 'type' not in course_data:
            course_data['type'] = 'paid' if float(course_data.get('price', 0)) > 0 else 'free'
            
        return course_data

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
        # Execute the delete. If there's an HTTP error, execute() should raise it.
        supabase_client.from_('courses').delete().eq('id', course_id).execute()
        # No need to check delete_response.error explicitly

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
        # Execute the query. If there's an HTTP error, execute() should raise it.
        response = supabase_client.from_('instructors').select('*').execute()
        # No need to check response.error explicitly in newer versions
        return response.data
    except Exception as e:
        # Log the specific error from Supabase or the client library
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
        
        # 1. First create auth user
        try:
            # Vérifier d'abord si l'email existe déjà
            existing = supabase_client.from_('instructors').select('email').eq('email', data['email']).execute()
            if existing.data and len(existing.data) > 0:
                raise ValueError(f"L'email {data['email']} existe déjà")

            # Créer l'utilisateur auth
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
                raise Exception("La création du compte a échoué - aucun utilisateur retourné")

            try:
                # Créer l'enregistrement instructeur
                instructor_data = {
                    'name': data['name'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'user_id': auth_response.user.id,
                    'status': data.get('status', 'active'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }

                # Insert instructor data
                insert_response = supabase_client.from_('instructors').insert(instructor_data).execute()

                # Check for insert errors (v2 raises exceptions, but explicit check is safer)
                if hasattr(insert_response, 'error') and insert_response.error:
                     raise Exception(f"Erreur Supabase lors de l'insertion: {insert_response.error.message}")

                # Select the newly created instructor data using user_id
                select_response = supabase_client.from_('instructors').select('*').eq('user_id', auth_response.user.id).single().execute()

                if hasattr(select_response, 'error') and select_response.error:
                    # If select fails, something is wrong, potentially rollback auth user? (Already handled in outer except)
                    raise Exception(f"Erreur Supabase lors de la sélection post-insertion: {select_response.error.message}")

                if not select_response.data:
                    # This shouldn't happen if insert succeeded and user_id is correct
                    raise Exception("Impossible de retrouver l'instructeur après création.")

                return select_response.data

            except Exception as e:
                # Nettoyage en cas d'erreur
                supabase_client.auth.admin.delete_user(auth_response.user.id)
                logger.error(f"Erreur création instructeur: {str(e)}")
                raise RuntimeError("Échec de la création de l'instructeur dans la base de données")

        except Exception as auth_error:
            logger.error(f"Auth user creation failed: {str(auth_error)}")
            raise Exception(f"Failed to create auth user: {str(auth_error)}")

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
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
