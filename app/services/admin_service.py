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
    - firebase_admin.firestore: For database operations
    - app.models.user: User model
    - app.models.course: Course model
    - app.models.student: Student model
    - app.models.instructor: Instructor model
    - app.database.firestore_db: Firestore database
    - firebase_admin.auth: For Firebase authentication
"""

from app.models import User, Course, Student, Instructor
from app.database.firestore_db import db
import logging
from datetime import datetime
import firebase_admin
from firebase_admin import auth, firestore

logger = logging.getLogger(__name__)

def get_dashboard_data_service():
    """Get statistics and data for the admin dashboard."""
    try:
        # Get references to collections
        students_ref = db.collection('students')
        courses_ref = db.collection('courses')
        instructors_ref = db.collection('instructors')

        # Get counts using get() instead of stream()
        students_docs = list(students_ref.stream())
        courses_docs = list(courses_ref.stream())
        instructors_docs = list(instructors_ref.stream())

        total_students = len(students_docs)
        total_courses = len(courses_docs)
        total_instructors = len(instructors_docs)

        # Get recent activities (last 5 items)
        recent_students = [
            {'id': doc.id, **doc.to_dict()} 
            for doc in students_ref.order_by('created_at', direction='DESCENDING').limit(5).stream()
        ]
        recent_courses = [
            {'id': doc.id, **doc.to_dict()} 
            for doc in courses_ref.order_by('created_at', direction='DESCENDING').limit(5).stream()
        ]

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
        students = []
        students_ref = db.collection('students')
        
        # Get all students
        for student_doc in students_ref.stream():
            try:
                student_data = student_doc.to_dict()
                if not student_data:  # Skip if document is empty
                    continue
                    
                student_data['id'] = student_doc.id
                
                try:
                    # Get student's enrollment using the new filter syntax
                    enrollments = list(
                        db.collection('enrollments')
                        .where('student_id', '==', student_doc.id)
                        .where('status', '==', 'active')
                        .limit(1)  # Only get the first active enrollment
                        .stream()
                    )
                    
                    # Get course information for the first active enrollment
                    if enrollments:
                        enrollment = enrollments[0]
                        enrollment_data = enrollment.to_dict()
                        
                        if enrollment_data and 'course_id' in enrollment_data:
                            course_ref = db.collection('courses').document(enrollment_data['course_id'])
                            course = course_ref.get()
                            
                            if course.exists:
                                course_data = course.to_dict()
                                if course_data:  # Only add if course data exists
                                    student_data['course'] = {
                                        'id': enrollment_data['course_id'],
                                        'title': course_data.get('title', 'Unknown Course')
                                    }
                
                except Exception as e:
                    logger.error(f"Error getting enrollment for student {student_doc.id}: {str(e)}")
                    # Continue with the next student even if there's an error with enrollments
                    
                # Ensure all required fields exist
                student_data.setdefault('name', 'Unknown')
                student_data.setdefault('email', '')
                student_data.setdefault('phone', '')
                student_data.setdefault('status', 'active')
                student_data.setdefault('created_at', None)
                
                students.append(student_data)
                
            except Exception as e:
                logger.error(f"Error processing student {student_doc.id}: {str(e)}")
                # Continue with next student if there's an error
                
        return students
        
    except Exception as e:
        logger.error(f"Error getting students: {str(e)}")
        raise ValueError(f"Failed to get students: {str(e)}")

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
                course_ref = db.collection('courses').document(course_id)
                course_doc = course_ref.get()
                if not course_doc.exists:
                    raise ValueError("Invalid course_id")
                course_data = course_doc.to_dict()
            except Exception as e:
                logger.error(f"Error validating course: {str(e)}")
                raise ValueError("Invalid course_id")

        # Create student document with transaction to ensure atomicity
        transaction = db.transaction()
        
        @firestore.transactional
        def create_student_in_transaction(transaction):
            # Create student document
            student_ref = db.collection('students').document()
            student_data = {
                'name': data['name'],
                'email': data['email'],
                'phone': data['phone'],
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            }
            transaction.set(student_ref, student_data)

            # If course_id is provided, create enrollment
            if course_id and course_data:
                enrollment_ref = db.collection('enrollments').document()
                enrollment_data = {
                    'student_id': student_ref.id,
                    'course_id': course_id,
                    'enrolled_at': firestore.SERVER_TIMESTAMP,
                    'status': 'active',
                    'course_title': course_data.get('title', 'Unknown Course')
                }
                transaction.set(enrollment_ref, enrollment_data)

                # Add course information to student data
                student_data['course'] = {
                    'id': course_id,
                    'title': course_data.get('title', 'Unknown Course')
                }

            return student_ref.id, student_data

        # Execute transaction
        student_id, student_data = create_student_in_transaction(transaction)
        
        # Return created student data
        created_student = student_data.copy()
        created_student['id'] = student_id
        return created_student

    except ValueError as e:
        logger.error(f"Validation error in create_student_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        raise

def update_student_service(student_id, data):
    """Update a student's information."""
    try:
        logger.info(f"Starting student update for ID: {student_id}")
        logger.debug(f"Update data received: {data}")

        # Validate student ID
        if not student_id:
            raise ValueError("Student ID is required")

        # Get student document reference
        student_ref = db.collection('students').document(student_id)
        student = student_ref.get()
        
        if not student.exists:
            raise ValueError(f"Student not found: {student_id}")
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Prepare update data
        update_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        logger.debug(f"Updating student document with data: {update_data}")
        
        try:
            # Update student document
            student_ref.update(update_data)
            logger.info(f"Successfully updated student document for ID: {student_id}")
        except Exception as e:
            logger.error(f"Error updating student document: {str(e)}")
            raise ValueError(f"Failed to update student document: {str(e)}")
        
        # Handle course assignment/update
        course_id = data.get('course_id')
        logger.debug(f"Processing course assignment. Course ID: {course_id}")
        
        try:
            # Get all current enrollments
            enrollments = list(
                db.collection('enrollments')
                .where('student_id', '==', student_id)
                .where('status', '==', 'active')
                .stream()
            )
            
            if course_id:
                # Verify course exists
                course_ref = db.collection('courses').document(course_id)
                course = course_ref.get()
                
                if not course.exists:
                    raise ValueError("Invalid course_id")
                
                course_data = course.to_dict()
                logger.debug(f"Found course data: {course_data}")
                
                if enrollments:
                    # Update existing enrollment
                    enrollment = enrollments[0]
                    enrollment_update = {
                        'course_id': course_id,
                        'updated_at': firestore.SERVER_TIMESTAMP,
                        'course_title': course_data.get('title', 'Unknown Course'),
                        'status': 'active'
                    }
                    logger.debug(f"Updating existing enrollment: {enrollment_update}")
                    enrollment.reference.update(enrollment_update)
                else:
                    # Create new enrollment
                    enrollment_data = {
                        'student_id': student_id,
                        'course_id': course_id,
                        'enrolled_at': firestore.SERVER_TIMESTAMP,
                        'status': 'active',
                        'course_title': course_data.get('title', 'Unknown Course')
                    }
                    logger.debug(f"Creating new enrollment: {enrollment_data}")
                    db.collection('enrollments').document().set(enrollment_data)
            else:
                # If no course_id is provided, deactivate existing enrollments
                logger.debug("No course_id provided, deactivating existing enrollments")
                for enrollment in enrollments:
                    enrollment.reference.update({
                        'status': 'inactive',
                        'updated_at': firestore.SERVER_TIMESTAMP
                    })
        
        except Exception as e:
            logger.error(f"Error handling course enrollment: {str(e)}")
            # Don't raise here, we want to return the updated student data even if course update fails
        
        # Get fresh student data for response
        student = student_ref.get()
        response_data = student.to_dict()
        response_data['id'] = student_id
        
        # Get current active enrollment if exists
        try:
            current_enrollment = next(
                (enrollment for enrollment in 
                 db.collection('enrollments')
                 .where('student_id', '==', student_id)
                 .where('status', '==', 'active')
                 .stream()), 
                None
            )
            
            if current_enrollment:
                enrollment_data = current_enrollment.to_dict()
                if enrollment_data and 'course_id' in enrollment_data:
                    course = db.collection('courses').document(enrollment_data['course_id']).get()
                    if course.exists:
                        course_data = course.to_dict()
                        response_data['course'] = {
                            'id': enrollment_data['course_id'],
                            'title': course_data.get('title', 'Unknown Course')
                        }
        except Exception as e:
            logger.error(f"Error getting current enrollment: {str(e)}")
            
        # Convert timestamps to strings for JSON serialization
        if 'created_at' in response_data and response_data['created_at']:
            response_data['created_at'] = response_data['created_at'].isoformat()
        if 'updated_at' in response_data and response_data['updated_at']:
            response_data['updated_at'] = response_data['updated_at'].isoformat()
            
        logger.info(f"Successfully completed student update for ID: {student_id}")
        return response_data
        
    except ValueError as e:
        logger.error(f"Validation error in update_student_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_student_service: {str(e)}")
        raise ValueError(f"Failed to update student: {str(e)}")

def delete_student_service(student_id):
    """Delete a student."""
    try:
        student_ref = db.collection('students').document(student_id)
        student = student_ref.get()
        if not student.exists:
            raise ValueError(f"Student with ID {student_id} not found")
        student_ref.delete()
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        raise

def get_courses_service():
    """Get list of all courses."""
    try:
        courses = []
        courses_ref = db.collection('courses')
        
        # Get all courses
        for course_doc in courses_ref.stream():
            course_data = course_doc.to_dict()
            course_data['id'] = course_doc.id
            
            # Get active student count for this course
            try:
                student_count = len(list(
                    db.collection('enrollments')
                    .where('course_id', '==', course_doc.id)
                    .where('status', '==', 'active')
                    .stream()
                ))
                course_data['student_count'] = student_count
            except Exception as e:
                logger.error(f"Error getting student count for course {course_doc.id}: {str(e)}")
                course_data['student_count'] = 0
            
            # Convert timestamps if they exist
            if 'created_at' in course_data and course_data['created_at']:
                course_data['created_at'] = course_data['created_at'].isoformat()
            if 'updated_at' in course_data and course_data['updated_at']:
                course_data['updated_at'] = course_data['updated_at'].isoformat()
            
            courses.append(course_data)
            
        return courses
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        raise ValueError(f"Failed to get courses: {str(e)}")

def create_course_service(data):
    """Create a new course."""
    try:
        # Validate required fields
        required_fields = ['title', 'description', 'instructor_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        # Special handling for price
        if 'price' not in data:
            missing_fields.append('price')
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate price
        try:
            price = float(data.get('price', 0))
            if price < 0:
                raise ValueError("Price cannot be negative")
        except (TypeError, ValueError) as e:
            logger.error(f"Price validation error: {str(e)}")
            raise ValueError("Invalid price value")

        # Verify instructor exists
        instructor_ref = db.collection('instructors').document(data['instructor_id'])
        instructor = instructor_ref.get()
        if not instructor.exists:
            raise ValueError(f"Instructor with ID {data['instructor_id']} not found")

        # Create course object with validated price
        new_course = Course(
            title=data['title'],
            description=data['description'],
            instructor_id=data['instructor_id'],
            price=price,
            status=data.get('status', 'active'),
            created_at=firestore.SERVER_TIMESTAMP,
            updated_at=firestore.SERVER_TIMESTAMP
        )

        # Add to Firestore
        course_ref = db.collection('courses').document()
        course_ref.set(new_course.to_dict())
        
        # Return created course with ID
        created_course = new_course.to_dict()
        created_course['id'] = course_ref.id
        
        # Add instructor name for convenience
        instructor_data = instructor.to_dict()
        created_course['instructor_name'] = instructor_data.get('name', 'Unknown')
        
        return created_course
        
    except ValueError as e:
        logger.error(f"Validation error in create_course_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise

def get_course_by_id_service(course_id):
    """Get a specific course by ID."""
    try:
        course_ref = db.collection('courses').document(course_id)
        course = course_ref.get()
        
        if not course.exists:
            return None
            
        course_data = course.to_dict()
        course_data['id'] = course_id
        
        # Get instructor name if not already in course data
        if 'instructor_name' not in course_data and 'instructor_id' in course_data:
            instructor_doc = db.collection('instructors').document(course_data['instructor_id']).get()
            if instructor_doc.exists:
                course_data['instructor_name'] = instructor_doc.to_dict().get('name', 'Unknown')
            else:
                course_data['instructor_name'] = 'Unknown'
                
        return course_data
    except Exception as e:
        logger.error(f"Error getting course by ID: {str(e)}")
        raise

def update_course_service(course_id, data):
    """Update an existing course."""
    try:
        course_ref = db.collection('courses').document(course_id)
        course = course_ref.get()
        
        if not course.exists:
            raise ValueError(f"Course with ID {course_id} not found")
            
        # Verify instructor exists if instructor_id is being updated
        if 'instructor_id' in data:
            instructor_ref = db.collection('instructors').document(data['instructor_id'])
            instructor = instructor_ref.get()
            if not instructor.exists:
                raise ValueError(f"Instructor with ID {data['instructor_id']} not found")
        
        # Convert price to float if provided
        if 'price' in data:
            data['price'] = float(data['price'])
            
        # Add updated timestamp
        data['updated_at'] = datetime.utcnow()
        
        # Update the course
        course_ref.update(data)
        
        # Get and return the updated course data
        updated_course = course_ref.get().to_dict()
        updated_course['id'] = course_id
        
        # Get instructor name if not already in course data
        if 'instructor_name' not in updated_course and 'instructor_id' in updated_course:
            instructor_doc = db.collection('instructors').document(updated_course['instructor_id']).get()
            if instructor_doc.exists:
                updated_course['instructor_name'] = instructor_doc.to_dict().get('name', 'Unknown')
            else:
                updated_course['instructor_name'] = 'Unknown'
                
        return updated_course
    except ValueError as e:
        logger.error(f"Validation error in update_course_service: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating course: {str(e)}")
        raise

def delete_course_service(course_id):
    """Delete a course."""
    try:
        course_ref = db.collection('courses').document(course_id)
        course = course_ref.get()
        if not course.exists:
            raise ValueError(f"Course with ID {course_id} not found")
        course_ref.delete()
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        raise

def get_instructors_service():
    """Get all instructors from Firestore."""
    try:
        instructors_ref = db.collection('instructors')
        instructors = []
        for doc in instructors_ref.stream():
            instructor_data = doc.to_dict()
            instructor_data['id'] = doc.id
            instructors.append(instructor_data)
        return instructors
    except Exception as e:
        logger.error(f"Error getting instructors: {str(e)}")
        raise Exception("Failed to retrieve instructors")

def create_instructor_service(data):
    """Create a new instructor in Firestore."""
    try:
        # Validate data
        required_fields = ['name', 'email', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f'حقل {field} مطلوب')

        # Log the service account being used
        try:
            app = firebase_admin.get_app()
            logger.info(f"Using Firebase app with project ID: {app.project_id}")
            logger.info(f"Service account email: {app._credentials.service_account_email}")
        except Exception as e:
            logger.error(f"Error getting Firebase app info: {str(e)}")

        # Check if instructor already exists
        instructor_ref = db.collection('instructors').where('email', '==', data['email']).get()
        if len(list(instructor_ref)) > 0:
            raise ValueError('مدرس بهذا البريد الإلكتروني موجود بالفعل')

        # Check if user already exists in Firebase Auth
        try:
            existing_user = auth.get_user_by_email(data['email'])
            if existing_user:
                raise ValueError('مستخدم بهذا البريد الإلكتروني موجود بالفعل')
        except auth.UserNotFoundError:
            pass  # This is expected if the user doesn't exist
        except Exception as e:
            logger.error(f"Error checking existing user: {str(e)}")
            raise ValueError('فشل في التحقق من وجود المستخدم')

        # Create Firebase auth user first
        try:
            logger.info(f"Creating Firebase user for email: {data['email']}")
            user = auth.create_user(
                email=data['email'],
                password=data['password'],
                display_name=data['name'],
                email_verified=False,
                disabled=False
            )
            logger.info(f"Successfully created Firebase user with UID: {user.uid}")
            
            # Add custom claims
            try:
                logger.info(f"Setting custom claims for user: {user.uid}")
                auth.set_custom_user_claims(user.uid, {'instructor': True})
                logger.info("Successfully set custom claims")
            except Exception as claims_error:
                logger.error(f"Error setting custom claims: {str(claims_error)}")
                # Don't raise here, continue with user creation
                
        except auth.UnauthenticatedError:
            logger.error("Firebase Admin SDK not properly authenticated")
            raise ValueError('خطأ في التحقق من صحة خدمة Firebase - يرجى التحقق من تكوين الخدمة')
        except auth.UnauthorizedError:
            logger.error("Firebase Admin SDK lacks necessary permissions")
            raise ValueError('خدمة Firebase تفتقر إلى الأذونات اللازمة - يرجى منح الأذونات المطلوبة')
        except Exception as e:
            logger.error(f"Error creating Firebase user: {str(e)}")
            raise ValueError('فشل في إنشاء حساب المدرس - ' + str(e))

        # Create instructor document
        instructor_data = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'specialties': data.get('specialties', []),
            'active': True,
            'uid': user.uid,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        logger.info(f"Creating Firestore document for instructor: {data['email']}")
        # Add instructor to Firestore
        instructor_ref = db.collection('instructors').document()
        instructor_ref.set(instructor_data)
        logger.info(f"Successfully created Firestore document with ID: {instructor_ref.id}")

        # Get the created instructor
        instructor = instructor_ref.get()
        return {**instructor.to_dict(), 'id': instructor.id}

    except ValueError as e:
        # Re-raise ValueError for expected errors
        raise
    except Exception as e:
        logger.error(f"Error creating instructor: {str(e)}")
        # If Firestore fails after Firebase auth success, try to clean up
        try:
            if 'user' in locals():
                logger.info(f"Cleaning up Firebase user after error: {user.uid}")
                auth.delete_user(user.uid)
                logger.info("Successfully cleaned up Firebase user")
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up Firebase user: {str(cleanup_error)}")
        raise Exception('حدث خطأ أثناء إنشاء المدرس')

def delete_instructor_service(email):
    """Delete an instructor from Firestore."""
    try:
        # Find instructor by email
        instructor_refs = db.collection('instructors').where('email', '==', email).limit(1).get()
        if not instructor_refs or len(instructor_refs) == 0:
            raise ValueError('المدرس غير موجود')

        instructor_doc = instructor_refs[0]
        instructor_data = instructor_doc.to_dict()

        # Delete Firebase auth user if uid exists
        if 'uid' in instructor_data:
            try:
                auth.delete_user(instructor_data['uid'])
            except Exception as e:
                logger.error(f"Error deleting Firebase user: {str(e)}")

        # Delete instructor document
        instructor_doc.reference.delete()

    except Exception as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        raise
