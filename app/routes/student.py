"""Student routes module."""

from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_auth
from app.services.assignment_service import (
    get_course_assignments,
    submit_assignment,
    get_student_progress
)
from app.services.student_service import get_student_profile, update_student_profile, enroll_student_in_course, get_student_courses
import logging

logger = logging.getLogger(__name__)
student_bp = Blueprint('student_api', __name__, url_prefix='/api/v1/student')


@student_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get the profile of the currently authenticated student.
    """
    try:
        student_id = g.user['user_id']
        profile = get_student_profile(student_id)
        if not profile:
            return jsonify({"error": "Student profile not found"}), 404
        return jsonify(profile), 200
    except Exception as e:
        logger.error(f"Error fetching student profile: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve profile"}), 500

@student_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update the profile of the currently authenticated student.
    """
    try:
        student_id = g.user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({"error": "No update data provided"}), 400
        
        updated_profile = update_student_profile(student_id, data)
        return jsonify(updated_profile), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error updating student profile: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to update profile"}), 500

@student_bp.route('/courses/<course_id>/enroll', methods=['POST'])
@require_auth
def enroll_in_course(course_id):
    """
    Enrolls the currently authenticated student in a course.
    """
    try:
        student_id = g.user['user_id']
        enrollment = enroll_student_in_course(student_id, course_id)
        return jsonify(enrollment), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400 # e.g., already enrolled or course not found
    except Exception as e:
        logger.error(f"Error enrolling student {student_id} in course {course_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to enroll in course"}), 500

@student_bp.route('/courses', methods=['GET'])
@require_auth
def list_student_courses():
    """
    Lists all courses the currently authenticated student is enrolled in.
    """
    try:
        student_id = g.user['user_id']
        courses = get_student_courses(student_id)
        return jsonify(courses), 200
    except Exception as e:
        logger.error(f"Error fetching courses for student {student_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve courses"}), 500

@student_bp.route('/assignments/<course_id>')
@require_auth
def get_assignments_api(course_id):
    """Get assignments for a course (API endpoint)."""
    try:
        assignments = get_course_assignments(course_id)
        return jsonify(assignments), 200
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500

@student_bp.route('/assignments/submit', methods=['POST'])
@require_auth
def submit_assignment_api():
    """Submit an assignment (API endpoint)."""
    try:
        data = request.get_json()
        # Get user_id from the g object populated by @require_auth
        student_id = g.user['user_id']
        
        if not data.get('assignment_id') or not data.get('submission_text'):
            return jsonify({'error': 'Missing required fields'}), 400

        submission = submit_assignment(
            assignment_id=data['assignment_id'],
            student_id=student_id,
            submission_text=data['submission_text']
        )
        return jsonify(submission), 201
    except Exception as e:
        logger.error(f"Error submitting assignment: {str(e)}")
        return jsonify({'error': 'Failed to submit assignment'}), 500

@student_bp.route('/progress/<course_id>')
@require_auth
def get_progress_api(course_id):
    """Get progress for a course (API endpoint)."""
    try:
        # Get user_id from the g object populated by @require_auth
        student_id = g.user['user_id']
        progress = get_student_progress(course_id, student_id)
        return jsonify(progress if progress else {}), 200
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({'error': 'Failed to get progress'}), 500