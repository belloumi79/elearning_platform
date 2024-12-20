"""
Course management routes module for the e-learning platform.

This module handles all course-related routes including course creation,
modification, deletion, and retrieval. All routes require admin authentication.

Routes:
    - /admin/courses: Course management page
    - /admin/api/courses: Course CRUD operations
    - /admin/api/courses/<course_id>: Individual course operations
    - /admin/api/instructors: Instructor listing
    - /api/courses: Public endpoint for fetching all courses
"""

from flask import Blueprint, jsonify, request, render_template, make_response
from flask_login import current_user
from app.middleware.auth import require_admin
from app.services.courses_service import CoursesService

courses_bp = Blueprint('courses', __name__)
courses_service = CoursesService()

@courses_bp.route('/admin/courses')
@require_admin
def courses_page():
    """Render the courses management page.
    
    Returns:
        str: Rendered HTML template for course management
    """
    return render_template('admin/courses.html')

@courses_bp.route('/admin/api/courses', methods=['GET'])
@require_admin
def get_courses():
    """Get all courses in the system.
    
    Returns:
        tuple: JSON response with list of courses and HTTP status code
        
    Raises:
        500: If there's an error retrieving courses
    """
    try:
        courses = courses_service.get_all_courses()
        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/api/user/enroll/', methods=['POST'])
def enroll_in_course():
    """Allows an authenticated user to enroll in a course.

    Expects a JSON payload with the `course_id`.

    Returns:
        A JSON response indicating success or failure, along with relevant data or error messages.
    """
    
    # Set CORS headers
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')  

    if request.method == 'OPTIONS':
        return response

    """
    try:
        data = request.get_json()
        course_id = data.get('course_id')

        if not course_id:
            return jsonify({'error': 'Missing course_id'}), 400

        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        user_id = current_user.id

        enrollment_result = courses_service.enroll_user_in_course(user_id, course_id)

        if enrollment_result['success']:
            return jsonify({'message': 'Successfully enrolled in course'}), 200, response.headers
        else:
            return jsonify({'error': enrollment_result['message']}), enrollment_result['status_code'], response.headers

    except Exception as e:
        return jsonify({'error': str(e)}), 500, response.headers

@courses_bp.route('/api/courses/<course_id>/enroll', methods=['POST'])
@require_admin
def enroll_student(course_id):
        
    Expected JSON payload:
    {
        "user_id": str
    }
    
    Returns:
        tuple: JSON response with enrollment data and HTTP status code
        
    Raises:
        400: If the request data is invalid
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        enrollment = courses_service.enroll_student_in_course(user_id, course_id)
        return jsonify(enrollment), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/admin/api/courses', methods=['POST'])
@require_admin
def create_course():
    """Create a new course.
    
    Expected JSON payload:
    {
        "title": str,
        "description": str,
        "instructor_id": str,
        "max_students": int,
        "start_date": str,
        "end_date": str
    }
    
    Returns:
        tuple: JSON response with created course data and HTTP status code
        
    Raises:
        400: If the request data is invalid
        500: If there an error creating the course
    """
    try:
        data = request.get_json()
        course = courses_service.create_course(data)
        return jsonify(course), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/admin/api/courses/<course_id>', methods=['GET'])
@require_admin
def get_course(course_id):
    """Get details of a specific course.
    
    Args:
        course_id (str): The ID of the course to retrieve
    
    Returns:
        tuple: JSON response with course data and HTTP status code
        
    Raises:
        404: If the course is not found
        500: If theren an error retrieving the course
    """
    try:
        course = courses_service.get_course_by_id(course_id)
        if course is None:
            return jsonify({'error': 'Course not found'}), 404
        return jsonify(course)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/admin/api/courses/<course_id>', methods=['PUT'])
@require_admin
def update_course(course_id):
    """Update an existing course.
    
    Args:
        course_id (str): The ID of the course to update
        
    Expected JSON payload:
    {
        "title": str,
        "description": str,
        "instructor_id": str,
        "max_students": int,
        "start_date": str,
        "end_date": str
    }
    
    Returns:
        tuple: JSON response with updated course data and HTTP status code
        
    Raises:
        404: If the course is not found
        400: If the request data is invalid
        500: If there an error updating the course
    """
    try:
        data = request.get_json()
        course = courses_service.update_course(course_id, data)
        if course is None:
            return jsonify({'error': 'Course not found'}), 404
        return jsonify(course)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/admin/api/courses/<course_id>', methods=['DELETE'])
@require_admin
def delete_course(course_id):
    """Delete a course.
    
    Args:
        course_id (str): The ID of the course to delete
    
    Returns:
        tuple: JSON response with success message and HTTP status code
        
    Raises:
        404: If the course is not found
        500: If there an error deleting the course
    """
    try:
        success = courses_service.delete_course(course_id)
        if not success:
            return jsonify({'error': 'Course not found'}), 404
        return jsonify({'message': 'Course deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/admin/api/instructors', methods=['GET'])
@require_admin
def get_instructors():
    """Get list of all instructors.
    
    Returns:
        tuple: JSON response with list of instructors and HTTP status code
        
    Raises:
        500: If there an error retrieving instructors
    """
    try:
        instructors = courses_service.get_all_instructors()
        return jsonify(instructors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/api/courses', methods=['GET'])
def get_all_courses_public():
    """
    Public endpoint for fetching all courses.

    Returns:
        tuple: JSON response with list of courses and HTTP status code

    Raises:
        500: If there's an error retrieving courses
    """
    try:
        courses = courses_service.get_all_courses()
        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
