"""Assignment and progress tracking services."""

from app.database.supabase_db import get_supabase_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_assignment(course_id, title, description, assignment_type, due_date=None, max_points=None, files=None, links=None):
    """Create a new assignment with optional files and links."""
    try:
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
        if not response.data:
            return None
            
        assignment = response.data[0]
        
        # Handle file uploads
        if files:
            for file in files:
                # Upload to Supabase storage
                file_path = f"assignments/{assignment['id']}/{file['filename']}"
                supabase.storage.from_('assignments').upload(
                    file_path,
                    file['content'],
                    {'content-type': 'application/octet-stream'}
                )
                
                # Create file record
                supabase.from_('assignment_files').insert({
                    'assignment_id': assignment['id'],
                    'file_name': file['filename'],
                    'file_path': file_path
                }).execute()
        
        # Handle links
        if links:
            for link in links:
                supabase.from_('assignment_links').insert({
                    'assignment_id': assignment['id'],
                    'url': link
                }).execute()
        
        return assignment
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
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
    
    return [{
        'student_name': sub['students']['name'],
        'course_title': sub['assignments']['courses']['title'],
        'assignment_title': sub['assignments']['title'],
        'submitted_at': sub['submitted_at'],
        'status': sub['status']
    } for sub in response.data]