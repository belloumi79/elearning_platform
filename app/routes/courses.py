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

from flask import Blueprint, jsonify, request, render_template
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
        500: If there's an error creating the course
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
        500: If there's an error retrieving the course
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
        500: If there's an error updating the course
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
        500: If there's an error deleting the course
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
        500: If there's an error retrieving instructors
    """
    try:
        instructors = courses_service.get_all_instructors()
        return jsonify(instructors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/api/courses', methods=['GET'])
def get_all_courses_public():
    """Get all courses in the system without authentication.
    
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
