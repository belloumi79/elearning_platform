"""Student routes module."""

from flask import Blueprint, render_template, request, jsonify
from app.middleware.auth import require_auth
from app.services.assignment_service import (
    get_course_assignments,
    submit_assignment,
    get_student_progress
)
import logging

logger = logging.getLogger(__name__)
student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@require_auth
def dashboard():
    """Render student dashboard."""
    return render_template('student/dashboard.html')

@student_bp.route('/assignments')
@require_auth
def assignments():
    """Render student assignments page."""
    course_id = request.args.get('course_id')
    return render_template('student/assignments.html', course_id=course_id)

@student_bp.route('/api/assignments/<course_id>')
@require_auth
def get_assignments_api(course_id):
    """Get assignments for a course (API endpoint)."""
    try:
        assignments = get_course_assignments(course_id)
        return jsonify(assignments), 200
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500

@student_bp.route('/api/assignments/submit', methods=['POST'])
@require_auth
def submit_assignment_api():
    """Submit an assignment (API endpoint)."""
    try:
        data = request.get_json()
        student_id = request.user['id']
        
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

@student_bp.route('/api/assignments/progress/<course_id>')
@require_auth
def get_progress_api(course_id):
    """Get progress for a course (API endpoint)."""
    try:
        student_id = request.user['id']
        progress = get_student_progress(course_id, student_id)
        return jsonify(progress if progress else {}), 200
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({'error': 'Failed to get progress'}), 500