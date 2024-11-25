"""
Admin routes module for the e-learning platform."""

from flask import Blueprint, jsonify, request, render_template, session
from app.middleware.auth import require_admin
from app.services.admin_service import (
    get_dashboard_data_service,
    get_students_service,
    create_student_service,
    update_student_service,
    delete_student_service,
    get_courses_service,
    create_course_service,
    update_course_service,
    delete_course_service,
    get_instructors_service,
    create_instructor_service,
    delete_instructor_service,
    get_course_by_id_service
)
import logging
from google.cloud import firestore
from google.cloud.firestore import transactional

logger = logging.getLogger(__name__)
db = firestore.Client()
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@require_admin
def admin_dashboard():
    """Render the admin dashboard page."""
    return render_template('admin/dashboard.html')

@admin_bp.route('/students')
@require_admin
def admin_students():
    """Render the student management page."""
    return render_template('admin/students.html')

@admin_bp.route('/courses')
@require_admin
def admin_courses():
    """Render the course management page."""
    return render_template('admin/courses.html')

@admin_bp.route('/instructors')
@require_admin
def instructors():
    """Render the instructor management page."""
    return render_template('admin/instructors.html')

@admin_bp.route('/api/dashboard-data')
@require_admin
def get_dashboard_data():
    """Get dashboard statistics and data."""
    try:
        data = get_dashboard_data_service()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء جلب بيانات لوحة التحكم'}), 500

@admin_bp.route('/api/students')
@require_admin
def get_students():
    """Get list of all students."""
    try:
        students = get_students_service()
        return jsonify(students), 200
    except ValueError as e:
        logger.error(f"Validation error in get_students: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting students: {str(e)}")
        return jsonify({"error": "Failed to get students"}), 500

@admin_bp.route('/api/students', methods=['POST'])
@require_admin
def create_student():
    """Create a new student."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Log the received data for debugging
        logger.debug(f"Received student data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        student = create_student_service(data)
        return jsonify(student), 201
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}")
        return jsonify({"error": "Failed to create student"}), 500

@admin_bp.route('/api/students/<student_id>', methods=['DELETE'])
@require_admin
def delete_student(student_id):
    """Delete a student."""
    try:
        delete_student_service(student_id)
        return jsonify({"message": "Student deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({"error": "Failed to delete student"}), 500

@admin_bp.route('/api/students/<student_id>', methods=['GET'])
@require_admin
def get_student(student_id):
    """Get a specific student by ID."""
    try:
        # Get student document
        student_ref = db.collection('students').document(student_id)
        student = student_ref.get()
        
        if not student.exists:
            return jsonify({"error": "Student not found"}), 404
            
        student_data = student.to_dict()
        student_data['id'] = student_id
        
        # Get student's enrollments
        enrollments = db.collection('enrollments').where('student_id', '==', student_id).stream()
        
        # Get course details if student is enrolled
        for enrollment in enrollments:
            enrollment_data = enrollment.to_dict()
            if 'course_id' in enrollment_data:
                course_ref = db.collection('courses').document(enrollment_data['course_id'])
                course = course_ref.get()
                if course.exists:
                    course_data = course.to_dict()
                    student_data['course'] = {
                        'id': enrollment_data['course_id'],
                        'title': course_data.get('title', 'Unknown Course')
                    }
                    break  # We'll just use the first active enrollment for now
        
        return jsonify(student_data), 200
    except Exception as e:
        logger.error(f"Error getting student: {str(e)}")
        return jsonify({"error": "Failed to get student"}), 500

@admin_bp.route('/api/students/<student_id>', methods=['PUT'])
@require_admin
def update_student(student_id):
    """Update a student's information."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        logger.info(f"Received update request for student {student_id}")
        logger.debug(f"Update data: {data}")
        
        try:
            updated_student = update_student_service(student_id, data)
            return jsonify(updated_student), 200
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            logger.error(f"Service error: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Route error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/api/courses')
@require_admin
def get_courses():
    """Get list of all courses."""
    try:
        courses = get_courses_service()
        return jsonify(courses), 200
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return jsonify({"error": "Failed to get courses"}), 500

@admin_bp.route('/api/courses', methods=['POST'])
@require_admin
def create_course():
    """Create a new course."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Log the received data for debugging
        logger.debug(f"Received course data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'description', 'instructor_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        # Special handling for price
        if 'price' not in data:
            missing_fields.append('price')
        elif data['price'] is None:  # Check if price is None
            missing_fields.append('price')
            
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Ensure price is a number
        try:
            data['price'] = float(data['price'])
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid price value"}), 400

        course = create_course_service(data)
        return jsonify(course), 201
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        return jsonify({"error": "Failed to create course"}), 500

@admin_bp.route('/api/courses/<course_id>', methods=['GET'])
@require_admin
def get_course(course_id):
    """Get a specific course by ID."""
    try:
        course = get_course_by_id_service(course_id)
        if course:
            return jsonify(course), 200
        return jsonify({"error": "Course not found"}), 404
    except Exception as e:
        logger.error(f"Error getting course: {str(e)}")
        return jsonify({"error": "Failed to get course"}), 500

@admin_bp.route('/api/courses/<course_id>', methods=['PUT'])
@require_admin
def update_course(course_id):
    """Update a course."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Log the received data for debugging
        logger.debug(f"Received course update data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'description', 'instructor_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        # Special handling for price
        if 'price' not in data:
            missing_fields.append('price')
        elif data['price'] is None:  # Check if price is None
            missing_fields.append('price')
            
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Ensure price is a number
        try:
            data['price'] = float(data['price'])
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid price value"}), 400

        course = update_course_service(course_id, data)
        return jsonify(course), 200
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating course: {str(e)}")
        return jsonify({"error": "Failed to update course"}), 500

@admin_bp.route('/api/courses/<course_id>', methods=['DELETE'])
@require_admin
def delete_course(course_id):
    """Delete a course."""
    try:
        delete_course_service(course_id)
        return jsonify({"message": "Course deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        return jsonify({"error": "Failed to delete course"}), 500

@admin_bp.route('/api/instructors', methods=['GET'])
@require_admin
def get_instructors():
    """Get list of all instructors."""
    try:
        instructors = get_instructors_service()
        return jsonify(instructors), 200
    except Exception as e:
        logger.error(f"Error getting instructors: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء جلب بيانات المدرسين'}), 500

@admin_bp.route('/api/instructors', methods=['POST'])
@require_admin
def add_instructor():
    """Create a new instructor."""
    try:
        logger.info("Received instructor creation request")
        logger.info(f"Request Content-Type: {request.content_type}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        logger.info(f"Request Data: {request.get_data(as_text=True)}")
        
        if not request.is_json:
            logger.warning(f"Invalid content type: {request.content_type}")
            return jsonify({
                'error': 'Content-Type must be application/json',
                'received_type': request.content_type
            }), 400
            
        data = request.get_json()
        if data is None:
            raw_data = request.get_data(as_text=True)
            logger.warning(f"Failed to parse JSON data. Raw data: {raw_data}")
            return jsonify({
                'error': 'Invalid JSON data',
                'raw_data': raw_data
            }), 400
            
        logger.info(f"Parsed JSON data: {data}")
        
        required_fields = ['name', 'email', 'phone', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({
                'error': 'حقول مطلوبة مفقودة',
                'missing_fields': missing_fields
            }), 400
        
        instructor = create_instructor_service(data)
        logger.info("Successfully created instructor")
        return jsonify(instructor), 201
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating instructor: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء إنشاء المدرس'}), 500

@admin_bp.route('/api/instructors/<email>', methods=['DELETE'])
@require_admin
def delete_instructor(email):
    """Delete an instructor."""
    try:
        delete_instructor_service(email)
        return '', 204
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting instructor: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء حذف المدرس'}), 500
