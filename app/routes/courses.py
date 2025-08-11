"""
Public Courses API Routes
-------------------------
This module provides public API endpoints for browsing courses.
"""
from flask import Blueprint, jsonify
from app.services.courses_service import get_courses_service, get_course_by_id_service
import logging

logger = logging.getLogger(__name__)
courses_bp = Blueprint('courses_api', __name__, url_prefix='/api/v1/courses')

@courses_bp.route('/', methods=['GET'])
def list_courses():
    """
    Get a list of all available courses.
    This is a public endpoint and does not require authentication.
    """
    try:
        courses = get_courses_service()
        return jsonify(courses), 200
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve courses"}), 500

@courses_bp.route('/<course_id>', methods=['GET'])
def get_course(course_id):
    """
    Get detailed information for a specific course by its ID.
    This is a public endpoint and does not require authentication.
    """
    try:
        course = get_course_by_id_service(course_id)
        if course:
            return jsonify(course), 200
        return jsonify({"error": "Course not found"}), 404
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve course"}), 500
