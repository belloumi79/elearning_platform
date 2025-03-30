from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging
import os
from supabase import create_client, Client
from postgrest import APIResponse  # Import for type hinting

logger = logging.getLogger(__name__)

class CoursesService:
    """
    Service class for managing course-related operations using Supabase.

    Attributes:
        supabase: Supabase client instance.
    """

    def __init__(self):
        """Initialize the courses service with Supabase client."""
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        # Use Service Role Key for backend operations if available and necessary
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key (Service Role or Anon) must be set in environment variables.")
            
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("CoursesService initialized with Supabase client.")

    def _handle_supabase_response(self, response: APIResponse, operation: str):
        """Helper to check for errors in Supabase responses."""
        # Supabase Python client v1.x might not have a dedicated error attribute.
        # Check status code or data structure based on library version.
        # Assuming v2.x+ structure for now:
        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error during {operation}: {response.error}")
             raise Exception(f"Supabase error during {operation}: {response.error.message}")
        # Fallback check for older versions or different structures
        if not response.data and operation != 'delete': # Delete might return empty data on success
             logger.warning(f"Supabase {operation} returned no data. Response: {response}")
             # Depending on context, this might be an error or just empty result
             # Raise cautiously or handle in calling function
             # raise Exception(f"Supabase {operation} failed or returned no data.")

    def get_all_courses(self) -> List[Dict]:
        """Retrieve all courses with instructor name and student count."""
        try:
            # 1. Get all courses
            courses_response = self.supabase.from_('courses').select('*').execute()
            self._handle_supabase_response(courses_response, "fetching courses")
            courses = courses_response.data

            if not courses:
                return []

            # 2. Get all instructors (for mapping names)
            instructors_response = self.supabase.from_('instructors').select('id, name').execute()
            self._handle_supabase_response(instructors_response, "fetching instructors")
            instructors_map = {instr['id']: instr['name'] for instr in instructors_response.data}

            # 3. Get all enrollments (for counting students per course)
            enrollments_response = self.supabase.from_('enrollments').select('course_id').execute()
            self._handle_supabase_response(enrollments_response, "fetching enrollments")
            student_counts = {}
            for enrollment in enrollments_response.data:
                course_id = enrollment['course_id']
                student_counts[course_id] = student_counts.get(course_id, 0) + 1

            # 4. Combine data
            enriched_courses = []
            for course in courses:
                course['instructor_name'] = instructors_map.get(course.get('instructor_id'), 'Unknown')
                course['student_count'] = student_counts.get(course['id'], 0)
                # Ensure datetime fields are strings if needed by frontend
                if isinstance(course.get('created_at'), datetime):
                    course['created_at'] = course['created_at'].isoformat()
                if isinstance(course.get('updated_at'), datetime):
                    course['updated_at'] = course['updated_at'].isoformat()
                enriched_courses.append(course)
                
            return enriched_courses

        except Exception as e:
            logger.error(f"Error in get_all_courses: {str(e)}")
            raise # Re-raise the exception

    def create_course(self, course_data: Dict) -> Dict:
        """Create a new course in Supabase."""
        required_fields = ['title', 'description', 'instructor_id', 'price']
        for field in required_fields:
            if field not in course_data or course_data[field] is None: # Check for None as well
                raise ValueError(f"Missing required field: {field}")

        try:
            price = float(course_data['price'])
            if price < 0:
                raise ValueError("Price cannot be negative")
            course_data['price'] = price
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid price: {str(e)}")

        try:
            # Validate instructor exists
            instructor_id = course_data['instructor_id']
            instructor_response = self.supabase.from_('instructors').select('id, name').eq('id', instructor_id).limit(1).execute()
            self._handle_supabase_response(instructor_response, f"validating instructor {instructor_id}")
            if not instructor_response.data:
                raise ValueError(f"Invalid instructor_id: {instructor_id}")
            instructor_name = instructor_response.data[0].get('name', 'Unknown')

            # Prepare data for Supabase (handle timestamps)
            now_iso = datetime.now(timezone.utc).isoformat()
            insert_data = {
                'title': course_data['title'],
                'description': course_data['description'],
                'instructor_id': instructor_id,
                'price': course_data['price'],
                'status': course_data.get('status', 'draft'),
                'created_at': now_iso,
                'updated_at': now_iso,
                # Add other fields like start_date, end_date if they exist in course_data
                'start_date': course_data.get('start_date'),
                'end_date': course_data.get('end_date'),
            }

            # Create course document
            response = self.supabase.from_('courses').insert(insert_data).execute()
            self._handle_supabase_response(response, "creating course")
            
            created_course = response.data[0] # Assuming insert returns the created row

            # Add derived fields for immediate return
            created_course['instructor_name'] = instructor_name
            created_course['student_count'] = 0 
            
            return created_course

        except (ValueError, Exception) as e:
            logger.error(f"Error creating course: {str(e)}")
            raise

    def update_course(self, course_id: str, course_data: Dict) -> Dict:
        """Update an existing course in Supabase."""
        if not course_id:
            raise ValueError("course_id is required for update.")
            
        update_payload = course_data.copy() # Avoid modifying original dict

        # Validate price if provided
        if 'price' in update_payload:
            try:
                price = float(update_payload['price'])
                if price < 0:
                    raise ValueError("Price cannot be negative")
                update_payload['price'] = price
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid price: {str(e)}")

        # Validate instructor if provided
        instructor_name = None
        if 'instructor_id' in update_payload:
             instructor_id = update_payload['instructor_id']
             instructor_response = self.supabase.from_('instructors').select('id, name').eq('id', instructor_id).limit(1).execute()
             self._handle_supabase_response(instructor_response, f"validating instructor {instructor_id} for update")
             if not instructor_response.data:
                 raise ValueError(f"Invalid instructor_id for update: {instructor_id}")
             instructor_name = instructor_response.data[0].get('name', 'Unknown')


        # Add updated_at timestamp
        update_payload['updated_at'] = datetime.now(timezone.utc).isoformat()

        try:
            response = self.supabase.from_('courses').update(update_payload).eq('id', course_id).execute()
            self._handle_supabase_response(response, f"updating course {course_id}")

            if not response.data:
                 raise ValueError(f"Course not found or update failed for ID: {course_id}")

            updated_course = response.data[0]

            # Fetch instructor name if not updated or already known
            if instructor_name is None:
                 instr_id = updated_course.get('instructor_id')
                 if instr_id:
                     instr_resp = self.supabase.from_('instructors').select('name').eq('id', instr_id).limit(1).execute()
                     if instr_resp.data:
                         instructor_name = instr_resp.data[0].get('name', 'Unknown')
            
            updated_course['instructor_name'] = instructor_name or 'Unknown'

            return updated_course

        except (ValueError, Exception) as e:
            logger.error(f"Error updating course {course_id}: {str(e)}")
            raise

    def delete_course(self, course_id: str) -> bool:
        """Delete a course and its related enrollments from Supabase."""
        if not course_id:
            raise ValueError("course_id is required for deletion.")
            
        try:
            # 1. Check if course exists (optional, delete is idempotent)
            # course_response = self.supabase.from_('courses').select('id').eq('id', course_id).limit(1).execute()
            # if not course_response.data:
            #     raise ValueError(f"Course not found: {course_id}")

            # 2. Delete related enrollments
            logger.info(f"Deleting enrollments for course {course_id}")
            enroll_delete_response = self.supabase.from_('enrollments').delete().eq('course_id', course_id).execute()
            # Don't raise error if enrollments don't exist, just log
            if hasattr(enroll_delete_response, 'error') and enroll_delete_response.error:
                 logger.error(f"Supabase error deleting enrollments for course {course_id}: {enroll_delete_response.error}")
                 # Decide if this should halt the course deletion
                 # raise Exception(f"Failed to delete enrollments: {enroll_delete_response.error.message}")

            # 3. Delete course
            logger.info(f"Deleting course {course_id}")
            course_delete_response = self.supabase.from_('courses').delete().eq('id', course_id).execute()
            self._handle_supabase_response(course_delete_response, f"deleting course {course_id}")
            
            # Check if deletion actually happened (response.data might be empty on success)
            # The check might depend on Supabase client version and settings (e.g., returning='minimal')
            logger.info(f"Course {course_id} deleted successfully.")
            return True

        except (ValueError, Exception) as e:
            logger.error(f"Error deleting course {course_id}: {str(e)}")
            raise

    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """Retrieve a specific course by ID from Supabase."""
        if not course_id:
            return None
            
        try:
            response = self.supabase.from_('courses').select('*').eq('id', course_id).limit(1).execute()
            self._handle_supabase_response(response, f"fetching course {course_id}")

            if not response.data:
                return None

            course = response.data[0]

            # Get instructor name
            instructor_name = 'Unknown'
            if course.get('instructor_id'):
                instr_resp = self.supabase.from_('instructors').select('name').eq('id', course['instructor_id']).limit(1).execute()
                if instr_resp.data:
                    instructor_name = instr_resp.data[0].get('name', 'Unknown')
            course['instructor_name'] = instructor_name

            # Get student count
            count_response = self.supabase.from_('enrollments').select('course_id', count='exact').eq('course_id', course_id).execute()
            course['student_count'] = count_response.count if hasattr(count_response, 'count') else 0
            
            # Ensure datetime fields are strings if needed
            if isinstance(course.get('created_at'), datetime):
                course['created_at'] = course['created_at'].isoformat()
            if isinstance(course.get('updated_at'), datetime):
                course['updated_at'] = course['updated_at'].isoformat()

            return course

        except Exception as e:
            logger.error(f"Error getting course by ID {course_id}: {str(e)}")
            raise

    def get_all_instructors(self) -> List[Dict]:
        """Retrieve all instructors from Supabase."""
        try:
            response = self.supabase.from_('instructors').select('*').execute()
            self._handle_supabase_response(response, "fetching all instructors")
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting all instructors: {str(e)}")
            raise

    def enroll_user_in_course(self, user_id: str, course_id: str) -> Dict:
        """Enroll a user in a course in Supabase."""
        if not user_id or not course_id:
            raise ValueError("user_id and course_id are required.")

        try:
            # 1. Validate course exists
            course_response = self.supabase.from_('courses').select('id').eq('id', course_id).limit(1).execute()
            self._handle_supabase_response(course_response, f"validating course {course_id} for enrollment")
            if not course_response.data:
                raise ValueError(f"Course not found: {course_id}")

            # 2. Validate user exists (optional - depends on whether user_id comes from auth or elsewhere)
            # user_response = self.supabase.from_('users').select('id').eq('id', user_id).limit(1).execute()
            # if not user_response.data:
            #     raise ValueError(f"User not found: {user_id}")

            # 3. Check if user is already enrolled
            enrollment_check = self.supabase.from_('enrollments') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('course_id', course_id) \
                .limit(1) \
                .execute()
            self._handle_supabase_response(enrollment_check, "checking existing enrollment")
            if enrollment_check.data:
                raise ValueError(f"User {user_id} is already enrolled in course {course_id}")

            # 4. Create enrollment document
            enrollment_data = {
                'user_id': user_id,
                'course_id': course_id,
                'enrolled_at': datetime.now(timezone.utc).isoformat()
            }
            response = self.supabase.from_('enrollments').insert(enrollment_data).execute()
            self._handle_supabase_response(response, "creating enrollment")

            if not response.data:
                 raise Exception("Failed to create enrollment, no data returned.")

            return response.data[0]

        except (ValueError, Exception) as e:
            logger.error(f"Error enrolling user {user_id} in course {course_id}: {str(e)}")
            raise

    # Alias for backward compatibility if needed
    enroll_student_in_course = enroll_user_in_course
