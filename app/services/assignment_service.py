"""Assignment and progress tracking services."""

from app.database.supabase_db import get_supabase_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_assignment(course_id, title, description, assignment_type, due_date=None, max_points=None, files=None, links=None):
    """Create a new assignment with optional files and links."""
    try:
        logger.info(f"Attempting to create assignment for course {course_id} with title '{title}'")
        supabase = get_supabase_client()

        # Create assignment record
        assignment_data = {
            'course_id': course_id,
            'title': title,
            'description': description,
            'assignment_type': assignment_type,
            'created_at': datetime.utcnow().isoformat(),
            'due_date': due_date,
            'max_points': max_points
        }

        response = supabase.from_('assignments').insert(assignment_data).execute()
        logger.debug(f"Supabase insert response: {response}") # Log response

        if not response.data:
            logger.error("Supabase insert failed or returned no data.")
            return None

        assignment = response.data[0]
        assignment_id = assignment.get('id') # Use .get() for safety
        if not assignment_id:
             logger.error("Assignment created but ID is missing in response data.")
             return None
        logger.info(f"Assignment record created with ID: {assignment_id}")

        # Handle file uploads
        if files:
            logger.info(f"Processing {len(files)} files for assignment {assignment_id}")
            for file in files:
                try:
                    # Upload to Supabase storage
                    file_path = f"assignments/{assignment_id}/{file['filename']}"
                    supabase.storage.from_('assignments').upload(
                        file_path,
                        file['content'],
                        {'content-type': 'application/octet-stream'}
                    )
                    logger.info(f"Uploaded file to storage: {file_path}")

                    # Create file record
                    supabase.from_('assignment_files').insert({
                        'assignment_id': assignment_id,
                        'file_name': file['filename'],
                        'file_path': file_path
                    }).execute()
                    logger.info(f"Created file record for: {file['filename']}")
                except Exception as file_error:
                    logger.error(f"Error processing file {file.get('filename', 'N/A')} for assignment {assignment_id}: {str(file_error)}")
                    # Decide if you want to continue or fail the whole assignment creation
                    # For now, let's log and return None to indicate failure
                    return None # Stop processing on file error

        # Handle links
        if links:
            logger.info(f"Processing {len(links)} links for assignment {assignment_id}")
            for link in links:
                try:
                    supabase.from_('assignment_links').insert({
                        'assignment_id': assignment_id,
                        'url': link
                    }).execute()
                    logger.info(f"Added link: {link}")
                except Exception as link_error:
                    logger.error(f"Error adding link {link} for assignment {assignment_id}: {str(link_error)}")
                    # Decide if you want to continue or fail
                    return None # Stop processing on link error

        logger.info(f"Successfully created assignment {assignment_id}")
        return assignment
    except Exception as e:
        logger.error(f"General error creating assignment: {str(e)}", exc_info=True) # Add exc_info for traceback
        return None

def get_course_assignments(course_id):
    """Get all assignments for a course."""
    supabase = get_supabase_client()
    response = supabase.from_('assignments') \
        .select('*') \
        .eq('course_id', course_id) \
        .order('created_at', descending=True) \
        .execute()
    return response.data

def submit_assignment(assignment_id, student_id, submission_text):
    """Submit an assignment."""
    supabase = get_supabase_client()

    submission_data = {
        'assignment_id': assignment_id,
        'student_id': student_id,
        'submission_text': submission_text,
        'submitted_at': datetime.utcnow().isoformat(),
        'status': 'submitted'
    }

    response = supabase.from_('assignment_submissions').insert(submission_data).execute()
    return response.data[0] if response.data else None

def grade_assignment(submission_id, grade, feedback=None):
    """Grade a submitted assignment."""
    supabase = get_supabase_client()

    grade_data = {
        'grade': grade,
        'graded_at': datetime.utcnow().isoformat(),
        'status': 'graded'
    }
    if feedback:
        grade_data['feedback'] = feedback

    response = supabase.from_('assignment_submissions') \
        .update(grade_data) \
        .eq('id', submission_id) \
        .execute()
    return response.data[0] if response.data else None

def track_progress(course_id, student_id):
    """Track student progress for a course."""
    return get_student_progress(course_id, student_id)

def get_student_progress(course_id, student_id):
    """Get student progress for a course."""
    supabase = get_supabase_client()

    # Get all assignments
    assignments = supabase.from_('assignments') \
        .select('id, title') \
        .eq('course_id', course_id) \
        .execute().data

    # Get submissions for each assignment
    progress = []
    if assignments: # Check if assignments list is not empty
        for assignment in assignments:
            submission = supabase.from_('assignment_submissions') \
                .select('*') \
                .eq('assignment_id', assignment['id']) \
                .eq('student_id', student_id) \
                .maybe_single() \
                .execute().data

            progress.append({
                'assignment_id': assignment['id'],
                'assignment_title': assignment['title'],
                'submitted': submission is not None,
                'submission': submission
            })

    return progress

def get_recent_progress(limit=10):
    """Get recent student progress across all courses."""
    supabase = get_supabase_client()

    response = supabase.from_('assignment_submissions') \
        .select('*, assignments!inner(title, courses!inner(title)), students!inner(name)') \
        .order('submitted_at', desc=True) \
        .limit(limit) \
        .execute()

    if not response.data:
        return [] # Return empty list if no data

    return [{
        'student_name': sub.get('students', {}).get('name', 'Unknown Student'), # Safer access
        'course_title': sub.get('assignments', {}).get('courses', {}).get('title', 'Unknown Course'), # Safer access
        'assignment_title': sub.get('assignments', {}).get('title', 'Unknown Assignment'), # Safer access
        'submitted_at': sub.get('submitted_at'),
        'status': sub.get('status')
    } for sub in response.data]