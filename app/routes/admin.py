"""Admin routes module for the e-learning platform."""

from flask import Blueprint, jsonify, request, render_template, session, current_app
from app.middleware.auth import require_admin
from app.services.auth_service import supabase_admin_login
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
from app.services.assignment_service import get_assignments_service
import logging
from flask import send_from_directory
logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(current_app.static_folder, filename)

@admin_bp.route('/api/login', methods=['POST'])
def admin_login():
    """Handle admin login requests."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Email and password are required'
            }), 400

        # Use existing supabase_admin_login function
        auth_result = supabase_admin_login(data['email'], data['password'])
        
        # Store user info and admin status in session
        session['user'] = {
            'id': auth_result['user_id'], # Assuming auth_result contains user_id
            'email': auth_result['email'],
            'isAdmin': auth_result['isAdmin']
        }
        session['access_token'] = auth_result['access_token']
        # Assuming refresh_token is also returned by supabase_admin_login
        if 'refresh_token' in auth_result:
             session['refresh_token'] = auth_result['refresh_token']
        session.modified = True # Mark session as modified

        logger.info(f"Admin login successful for user {auth_result['user_id']}. Session updated.")

        return jsonify({
            'success': True,
            'message': 'Login successful' # No need to send token/user back in JSON if using session
        }), 200

    except ValueError as e:
        return jsonify({
            'error': str(e)
        }), 401
    except Exception as e:
        return jsonify({
            'error': f'Login failed: {str(e)}'
        }), 500

@admin_bp.route('/dashboard')
@require_admin
def admin_dashboard():
    """Render the admin dashboard page."""
    return render_template('admin/dashboard.html')

@admin_bp.route('/students')
@require_admin
def admin_students():
    """Render the student management page with Supabase credentials."""
    supabase_url = current_app.config.get('SUPABASE_URL')
    supabase_key = current_app.config.get('SUPABASE_KEY')
    return render_template('admin/students.html',
                           supabase_url=supabase_url,
                           supabase_key=supabase_key)

@admin_bp.route('/courses')
@require_admin
def admin_courses():
    """Render the course management page."""
    return render_template('admin/courses.html')

@admin_bp.route('/assignments')
@require_admin
def admin_assignments():
    """Render the main assignments management page."""
    return render_template('admin/assignments.html')

@admin_bp.route('/api/assignments')
@require_admin
def get_assignments():
    """Get all assignments."""
    try:
        assignments = get_assignments_service()
        return jsonify(assignments), 200
    except Exception as e:
        logger.error(f"Error getting assignments: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500
@admin_bp.route('/api/courses/<course_id>/assignments')
@require_admin
def get_course_assignments_api(course_id):
    """Get assignments for a specific course (admin API)."""
    try:
        from app.services.assignment_service import get_course_assignments
        assignments = get_course_assignments(course_id)
        return jsonify(assignments), 200
    except Exception as e:
        logger = current_app.logger
        logger.error(f"Error getting assignments for course {course_id}: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500


@admin_bp.route('/courses/<course_id>/assignments')
@require_admin
def course_assignments(course_id):
    """Render the assignments management page for a course."""
    return render_template('admin/assignments.html', course_id=course_id)

@admin_bp.route('/courses/<course_id>/assignments/new', methods=['GET', 'POST'])
@require_admin
def new_assignment_form(course_id):
    """Render the form to create a new assignment for a specific course, or handle form submission."""
    if request.method == 'POST':
        # Extract form data
        title = request.form.get('assignmentTitle')
        description = request.form.get('assignmentDescription')
        assignment_type = request.form.get('assignmentType')
        due_date = request.form.get('dueDate')
        max_points = request.form.get('maxPoints')
        # TODO: Handle file uploads and external links if needed
        try:
            from app.services.assignment_service import create_assignment
            assignment = create_assignment(
                course_id=course_id,
                title=title,
                description=description,
                assignment_type=assignment_type,
                due_date=due_date,
                max_points=max_points,
                # Add file handling and links if needed
            )
            return jsonify({'success': True, 'assignment': assignment}), 201
        except Exception as e:
            logger = current_app.logger
            logger.error(f"Error creating assignment: {str(e)}")
            return jsonify({'error': 'Failed to create assignment'}), 500
    # GET: render the form
    return render_template('admin/new_assignment.html', course_id=course_id)

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


@admin_bp.route('/api/assignments/recent')
@require_admin
def recent_assignments():
    """Get all assignments for dashboard."""
    try:
        assignments = get_assignments_service()
        return jsonify(assignments), 200
    except Exception as e:
        logger.error(f"Error getting all assignments: {str(e)}")
        return jsonify({'error': 'Failed to get assignments'}), 500


@admin_bp.route('/api/progress/recent')
@require_admin
def recent_progress():
    """Get recent student progress for dashboard."""
    try:
        supabase = get_supabase_client()
        response = supabase.from_('course_progress') \
            .select('*, students(name), courses(title)') \
            .order('last_accessed', desc=True) \
            .limit(10) \
            .execute()
        
        progress = [{
            'student_name': p['students']['name'] if p['students'] else 'غير معروف',
            'course_title': p['courses']['title'] if p['courses'] else 'غير معروف',
            'progress_percentage': p['progress_percentage'],
            'completed': p['completed']
        } for p in response.data]
        
        return jsonify(progress)
    except Exception as e:
        logger.error(f"Error getting recent progress: {str(e)}")
        return jsonify({'error': 'Failed to get progress data'}), 500

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

@admin_bp.route('/api/courses/<course_id>/assignments/<assignment_id>', methods=['PUT'])
@require_admin
def update_assignment(course_id, assignment_id):
    """Update an existing assignment."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided for update"}), 400

        logger.info(f"Attempting to update assignment {assignment_id} in course {course_id}")
        # Assuming update_assignment_service takes assignment_id and data
        updated_assignment = update_assignment_service(assignment_id, data)
        return jsonify(updated_assignment), 200

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating assignment: {str(e)}")
        return jsonify({"error": "Failed to update assignment"}), 500

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
    # TODO: Refactor this function to use Supabase instead of Firestore
    # try:
    #     # Get student document
    #     student_ref = db.collection('students').document(student_id)
    #     student = student_ref.get()
        
    #     if not student.exists:
    #         return jsonify({"error": "Student not found"}), 404
            
    #     student_data = student.to_dict()
    #     student_data['id'] = student_id
        
    #     # Get student's enrollments
    #     enrollments = db.collection('enrollments').where('student_id', '==', student_id).stream()
        
    #     # Get course details if student is enrolled
    #     for enrollment in enrollments:
    #         enrollment_data = enrollment.to_dict()
    #         if 'course_id' in enrollment_data:
    #             course_ref = db.collection('courses').document(enrollment_data['course_id'])
    #             course = course_ref.get()
    #             if course.exists:
    #                 course_data = course.to_dict()
    #                 student_data['course'] = {
    #                     'id': enrollment_data['course_id'],
    #                     'title': course_data.get('title', 'Unknown Course')
    #                 }
    #                 break  # We'll just use the first active enrollment for now
        
    #     return jsonify(student_data), 200
    # except Exception as e:
    #     logger.error(f"Error getting student: {str(e)}")
    #     return jsonify({"error": "Failed to get student"}), 500
    logger.warning(f"Route /api/students/{student_id} GET needs refactoring for Supabase")
    return jsonify({"error": "Endpoint not fully implemented for Supabase yet"}), 501


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
        
        # --- Validation ---
        # Check required fields (must exist and not be empty strings)
        required_fields = ['title', 'instructor_id']
        missing_or_empty = [
            field for field in required_fields
            if data.get(field) is None or str(data.get(field)).strip() == ''
        ]
        if missing_or_empty:
            return jsonify({
                "error": f"Missing or empty required fields: {', '.join(missing_or_empty)}"
            }), 400

        # --- Data Processing ---
        # Handle optional description (default to empty string if missing/None/empty)
        data['description'] = str(data.get('description', '')).strip()

        # Handle price based on 'type' field and check for empty string
        if data.get('type') == 'free':
            data['price'] = 0.0
        # Check for missing, None, or empty string for price before attempting conversion
        elif data.get('price') is None or str(data.get('price')).strip() == '':
             data['price'] = 0.0
        else:
             # If not free and price is provided, validate it
             try:
                 price_value = float(str(data['price']).strip())
                 if price_value < 0:
                      return jsonify({"error": "Price cannot be negative"}), 400
                 data['price'] = price_value # Assign validated float
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
        
        # --- Validation ---
        # Check required fields (must exist and not be empty strings)
        required_fields = ['title', 'instructor_id']
        missing_or_empty = [
            field for field in required_fields
            if data.get(field) is None or str(data.get(field)).strip() == ''
        ]
        if missing_or_empty:
            return jsonify({
                "error": f"Missing or empty required fields: {', '.join(missing_or_empty)}"
            }), 400

        # --- Data Processing ---
        # Handle optional description (default to empty string if missing/None/empty)
        # Use get with default '' and strip potential whitespace
        data['description'] = str(data.get('description', '')).strip()

        # Handle price based on 'type' field and check for empty string
        if data.get('type') == 'free':
            data['price'] = 0.0
        # Check for missing, None, or empty string for price before attempting conversion
        elif data.get('price') is None or str(data.get('price')).strip() == '':
             data['price'] = 0.0
        else:
             # If not free and price is provided, validate it
             try:
                 price_value = float(str(data['price']).strip())
                 if price_value < 0:
                      return jsonify({"error": "Price cannot be negative"}), 400
                 data['price'] = price_value # Assign validated float
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
