"""Assignment and progress tracking routes."""

from flask import Blueprint, jsonify, request, current_app
from app.middleware.auth import require_admin, require_auth
from app.services.assignment_service import (
    create_assignment,
    get_course_assignments,
    submit_assignment,
    update_assignment,
    grade_assignment,
    track_progress,
    get_student_progress,
    delete_assignment,
    get_assignment_by_id,
    get_recent_assignments_service
)
import logging

logger = logging.getLogger(__name__)

assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')

from werkzeug.utils import secure_filename
from datetime import datetime
import os

@assignments_bp.route('/test-upload', methods=['POST'])
def test_upload():
    """Test endpoint for file upload verification"""
    try:
        from app.database.supabase_db import get_supabase_client
        supabase = get_supabase_client()

        # Test file upload
        test_content = b'This is a test file'
        upload_response = supabase.storage.from_('assignments').upload(
            'test-upload.txt',
            test_content,
            {'content-type': 'text/plain'}
        )

        # Handle UploadResponse object
        if hasattr(upload_response, 'path'):
            return jsonify({'message': 'Test upload successful', 'path': upload_response.path}), 200
        elif isinstance(upload_response, dict) and upload_response.get('Key'):
            return jsonify({
                'message': 'Test upload successful',
                'path': upload_response['Key']
            }), 200
        else:
            logger.error(f"Unexpected response format: {str(upload_response)}")
            return jsonify({'error': 'Upload verification failed'}), 500

    except Exception as e:
        logger.error(f"Test upload error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500