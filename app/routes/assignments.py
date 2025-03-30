"""Assignment and progress tracking routes."""

from flask import Blueprint, jsonify, request
from app.middleware.auth import require_admin, require_auth
from app.services.assignment_service import (
    create_assignment,
    get_course_assignments,
    submit_assignment,
    grade_assignment,
    track_progress,
    get_student_progress
)
import logging

logger = logging.getLogger(__name__)
assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')

from werkzeug.utils import secure_filename
from datetime import datetime
import os

@assignments_bp.route('/<course_id>', methods=['POST'])
@require_admin
def create_course_assignment(course_id):
    """Create a new assignment with optional files and links."""
    try:
        # Handle form data
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'assignment_type': request.form.get('assignment_type'),
            'due_date': request.form.get('due_date'),
            'max_points': request.form.get('max_points'),
            'links': request.form.getlist('links[]')
        }

        # Validate required fields
        required_fields = ['title', 'assignment_type']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Handle file uploads
        files = []
        if 'files' in request.files:
            for file in request.files.getlist('files'):
                if file.filename != '':
                    files.append({
                        'filename': secure_filename(file.filename),
                        'content': file.read()
                    })

        # Create assignment
        assignment = create_assignment(
            course_id=course_id,
            title=data['title'],
            description=data.get('description', ''),
            assignment_type=data['assignment_type'],
            due_date=data.get('due_date'),
            max_points=data.get('max_points'),
            files=files,
            links=data.get('links', [])
        )
        return jsonify(assignment), 201
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        return jsonify({'error': 'Failed to create assignment'}), 500

@assignments_bp.route('/<course_id>', methods=['GET'])
@require_auth
def get_assignments(course_id):
    """Get all assignments for a course."""
    try:
        # Verify user has access to this course
        supabase = get_supabase_client()
        enrollment = supabase.from_('enrollments') \
            .select('*') \
            .eq('course_id', course_id) \
            .eq('student_id', request.user['id']) \
            .maybe_single() \
            .execute()
            
        if not enrollment.data and not request.user.get('isAdmin', False):
            return jsonify({'error': 'Unauthorized access'}), 403

        assignments = get_course_assignments(course_id)
        return jsonify(assignments), 200
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500

@assignments_bp.route('/<assignment_id>/submit', methods=['POST'])
@require_auth
def submit_assignment_route(assignment_id):
    """Submit an assignment."""
    try:
        data = request.get_json()
        student_id = request.user['id']  # From auth middleware
        
        if not data.get('submission_text'):
            return jsonify({'error': 'Submission text is required'}), 400

        submission = submit_assignment(
            assignment_id=assignment_id,
            student_id=student_id,
            submission_text=data['submission_text']
        )
        return jsonify(submission), 201
    except Exception as e:
        logger.error(f"Error submitting assignment: {str(e)}")
        return jsonify({'error': 'Failed to submit assignment'}), 500

@assignments_bp.route('/submissions/<submission_id>/grade', methods=['PUT'])
@require_admin
def grade_submission(submission_id):
    """Grade a submitted assignment."""
    try:
        data = request.get_json()
        if 'grade' not in data:
            return jsonify({'error': 'Grade is required'}), 400

        graded = grade_assignment(
            submission_id=submission_id,
            grade=data['grade'],
            feedback=data.get('feedback', '')
        )
        return jsonify(graded), 200
    except Exception as e:
        logger.error(f"Error grading assignment: {str(e)}")
        return jsonify({'error': 'Failed to grade assignment'}), 500

@assignments_bp.route('/progress/<course_id>', methods=['POST'])
@require_auth
def update_progress(course_id):
    """Update course progress for a student."""
    try:
        data = request.get_json()
        student_id = request.user['id']  # From auth middleware
        
        if 'progress_percentage' not in data:
            return jsonify({'error': 'Progress percentage is required'}), 400

        progress = track_progress(
            course_id=course_id,
            student_id=student_id,
            progress_percentage=data['progress_percentage']
        )
        return jsonify(progress), 200
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        return jsonify({'error': 'Failed to update progress'}), 500

@assignments_bp.route('/progress/<course_id>', methods=['GET'])
@require_auth
def get_progress(course_id):
    """Get progress for a student in a course."""
    try:
        student_id = request.user['id']  # From auth middleware
        progress = get_student_progress(course_id, student_id)
        return jsonify(progress if progress else {}), 200
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({'error': 'Failed to get progress'}), 500