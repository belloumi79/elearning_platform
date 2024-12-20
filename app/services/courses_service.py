from typing import Dict, List, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import firestore

class CoursesService:
    """
    Service class for managing course-related operations.

    This class provides methods for course CRUD operations and enrollment
    management. It maintains connections to the necessary Firestore
    collections and handles all database interactions.

    Attributes:
        db: Firestore client instance
        courses_ref: Reference to courses collection
        instructors_ref: Reference to instructors collection
    """

    def __init__(self):
        """Initialize the courses service with database connections."""
        self.db = firestore.client()
        self.courses_ref = self.db.collection('courses')
        self.instructors_ref = self.db.collection('instructors')

    def get_all_courses(self) -> List[Dict]:
        """
        Retrieve all courses with additional metadata.

        Fetches all courses and enriches them with:
        - Instructor information
        - Student enrollment count
        - Course status and metadata

        Returns:
            List[Dict]: List of course dictionaries, each containing:
                - id (str): Course unique identifier
                - title (str): Course title
                - description (str): Course description
                - instructor_id (str): ID of course instructor
                - instructor_name (str): Name of course instructor
                - price (float): Course price
                - student_count (int): Number of enrolled students
                - status (str): Course status
                - created_at (timestamp): Creation timestamp
                - updated_at (timestamp): Last update timestamp
        """
        courses = []
        for doc in self.courses_ref.stream():
            course = doc.to_dict()
            course['id'] = doc.id
            # Get instructor name
            if 'instructor_id' in course:
                instructor_doc = self.instructors_ref.document(course['instructor_id']).get()
                if instructor_doc.exists:
                    course['instructor_name'] = instructor_doc.to_dict().get('name', 'Unknown')
                else:
                    course['instructor_name'] = 'Unknown'
            # Get student count
            enrollments = self.db.collection('enrollments')\
                .where('course_id', '==', doc.id)\
                .get()
            course['student_count'] = len(enrollments)
            courses.append(course)
        return courses

    def create_course(self, course_data: Dict) -> Dict:
        """
        Create a new course in the database.

        Args:
            course_data (Dict): Course information containing:
                - title (str): Course title
                - description (str): Course description
                - instructor_id (str): ID of assigned instructor
                - price (float): Course price
                - status (str, optional): Course status
                - start_date (datetime, optional): Course start date
                - end_date (datetime, optional): Course end date

        Returns:
            Dict: Created course data including generated ID

        Raises:
            ValueError: If required fields are missing or invalid
            Exception: If there's an error creating the course
        """
        required_fields = ['title', 'description', 'instructor_id', 'price']
        for field in required_fields:
            if field not in course_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate price
        try:
            price = float(course_data['price'])
            if price < 0:
                raise ValueError("Price cannot be negative")
            course_data['price'] = price
        except ValueError as e:
            raise ValueError(f"Invalid price: {str(e)}")

        # Validate instructor exists
        instructor_doc = self.instructors_ref.document(course_data['instructor_id']).get()
        if not instructor_doc.exists:
            raise ValueError("Invalid instructor_id")

        instructor_data = instructor_doc.to_dict()
        instructor_name = instructor_data.get('name', 'Unknown')

        # Add metadata
        course_data['created_at'] = firestore.SERVER_TIMESTAMP
        course_data['updated_at'] = firestore.SERVER_TIMESTAMP
        course_data['status'] = course_data.get('status', 'draft')
        course_data['instructor_name'] = instructor_name

        # Create course document
        doc_ref = self.courses_ref.document()
        doc_ref.set(course_data)

        # Return created course data
        created_course = course_data.copy()
        created_course['id'] = doc_ref.id
        created_course['student_count'] = 0

        return created_course

    def update_course(self, course_id: str, course_data: Dict) -> Dict:
        """
        Update an existing course.

        Args:
            course_id (str): Course unique identifier
            course_data (Dict): Updated course information, may include:
                - title (str): New course title
                - description (str): New course description
                - price (float): New course price
                - status (str): New course status
                - start_date (datetime): New start date
                - end_date (datetime): New end date

        Returns:
            Dict: Updated course data

        Raises:
            ValueError: If course_id is invalid or data is invalid
            Exception: If there's an error updating the course
        """
        # Validate course exists
        course_ref = self.courses_ref.document(course_id)
        course_doc = course_ref.get()
        if not course_doc.exists:
            raise ValueError(f"Course not found: {course_id}")

        # Validate price if provided
        if 'price' in course_data:
            try:
                price = float(course_data['price'])
                if price < 0:
                    raise ValueError("Price cannot be negative")
                course_data['price'] = price
            except ValueError as e:
                raise ValueError(f"Invalid price: {str(e)}")

        # Update metadata
        course_data['updated_at'] = firestore.SERVER_TIMESTAMP

        # Update course
        course_ref.update(course_data)

        # Return updated course data
        updated_course = course_ref.get().to_dict()
        updated_course['id'] = course_id

        # Get instructor name
        if 'instructor_id' in updated_course:
            instructor_doc = self.instructors_ref.document(updated_course['instructor_id']).get()
            if instructor_doc.exists:
                updated_course['instructor_name'] = instructor_doc.to_dict().get('name', 'Unknown')
            else:
                updated_course['instructor_name'] = 'Unknown'

        return updated_course

    def delete_course(self, course_id: str) -> bool:
        """
        Delete a course and its related data.

        This operation will:
        1. Delete the course document
        2. Delete all related enrollments
        3. Update instructor's course count

        Args:
            course_id (str): Course unique identifier

        Returns:
            bool: True if deletion was successful

        Raises:
            ValueError: If course_id is invalid
            Exception: If there's an error during deletion
        """
        # Validate course exists
        course_ref = self.courses_ref.document(course_id)
        if not course_ref.get().exists:
            raise ValueError(f"Course not found: {course_id}")

        # Delete related enrollments
        enrollments = self.db.collection('enrollments')\
            .where('course_id', '==', course_id)\
            .stream()
        for enrollment in enrollments:
            enrollment.reference.delete()

        # Delete course
        course_ref.delete()
        return True

    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """
        Retrieve a specific course by ID.

        Args:
            course_id: The ID of the course to retrieve
        Returns:
            Dictionary containing the course data or None if not found
        """
        doc = self.courses_ref.document(course_id).get()
        if not doc.exists:
            return None

        course = doc.to_dict()
        course['id'] = doc.id

        # Get instructor name
        if 'instructor_id' in course:
            instructor_doc = self.instructors_ref.document(course['instructor_id']).get()
            if instructor_doc.exists:
                course['instructor_name'] = instructor_doc.to_dict().get('name', 'Unknown')
            else:
                course['instructor_name'] = 'Unknown'

        # Get student count
        enrollments = self.db.collection('enrollments')\
            .where('course_id', '==', course_id)\
            .get()
        course['student_count'] = len(enrollments)

        return course

    def get_all_instructors(self) -> List[Dict]:
        """
        Retrieve all instructors from the database.
        Returns:
            List of instructor dictionaries
        """
        instructors = []
        for doc in self.instructors_ref.stream():
            instructor = doc.to_dict()
            instructor['id'] = doc.id
            instructors.append(instructor)
        return instructors

    def enroll_student_in_course(self, user_id: str, course_id: str) -> Dict:
        """
        Enroll a student in a course.

        Args:
            user_id (str): The ID of the user to enroll
            course_id (str): The ID of the course to enroll in

        Returns:
            Dict: Enrollment data

        Raises:
            ValueError: If user or course is invalid or user is already enrolled
            Exception: If there's an error during enrollment
        """
        # Validate course exists
        course_ref = self.courses_ref.document(course_id)
        if not course_ref.get().exists:
            raise ValueError(f"Course not found: {course_id}")

        # Validate user exists (basic check, assuming user service handles this)
        # In a real app, you'd fetch the user document to validate

        # Check if user is already enrolled
        enrollment_ref = self.db.collection('enrollments')\
            .where('user_id', '==', user_id)\
            .where('course_id', '==', course_id)\
            .get()
        if len(enrollment_ref) > 0:
            raise ValueError(f"User {user_id} is already enrolled in course {course_id}")

        # Create enrollment document
        enrollment_data = {
            'user_id': user_id,
            'course_id': course_id,
            'enrolled_at': firestore.SERVER_TIMESTAMP
        }
        enrollment_doc_ref = self.db.collection('enrollments').document()
        enrollment_doc_ref.set(enrollment_data)

        # Return enrollment data
        enrollment_data['id'] = enrollment_doc_ref.id
        return enrollment_data

    def enroll_user_in_course(self, user_id: str, course_id: str) -> Dict:
        """
        Enroll a user in a course.

        Args:
            user_id (str): The ID of the user to enroll
            course_id (str): The ID of the course to enroll in

        Returns:
            Dict: Enrollment data

        Raises:
            ValueError: If user or course is invalid or user is already enrolled
            Exception: If there's an error during enrollment
        """
        # Validate course exists
        course_ref = self.courses_ref.document(course_id)
        if not course_ref.get().exists:
            raise ValueError(f"Course not found: {course_id}")

        # Validate user exists (basic check, assuming user service handles this)
        # In a real app, you'd fetch the user document to validate

        # Check if user is already enrolled
        enrollment_ref = self.db.collection('enrollments')\
            .where('user_id', '==', user_id)\
            .where('course_id', '==', course_id)\
            .get()
        if len(enrollment_ref) > 0:
            raise ValueError(f"User {user_id} is already enrolled in course {course_id}")

        # Create enrollment document
        enrollment_data = {
            'user_id': user_id,
            'course_id': course_id,
            'enrolled_at': firestore.SERVER_TIMESTAMP
        }
        enrollment_doc_ref = self.db.collection('enrollments').document()
        enrollment_doc_ref.set(enrollment_data)

        # Return enrollment data
        enrollment_data['id'] = enrollment_doc_ref.id
        return enrollment_data
