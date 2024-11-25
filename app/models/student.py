"""Student model for the e-learning platform."""

from datetime import datetime

class Student:
    """Student model class representing a student in the platform."""

    def __init__(self, name, email, phone, level=None, enrolled_courses=None,
                 created_at=None, updated_at=None, status="active"):
        """
        Initialize a new Student instance.

        Args:
            name (str): Student's full name
            email (str): Student's email address
            phone (str): Student's phone number
            level (str, optional): Student's current level
            enrolled_courses (list, optional): List of enrolled course IDs
            created_at (datetime, optional): Creation timestamp. Defaults to current time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current time.
            status (str, optional): Student status. Defaults to "active".
        """
        self.name = name
        self.email = email
        self.phone = phone
        self.level = level
        self.enrolled_courses = enrolled_courses or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status = status

    def to_dict(self):
        """
        Convert the Student instance to a dictionary.

        Returns:
            dict: Dictionary representation of the student
        """
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'level': self.level,
            'enrolled_courses': self.enrolled_courses,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        """
        Create a Student instance from a dictionary.

        Args:
            data (dict): Dictionary containing student data

        Returns:
            Student: New Student instance
        """
        return Student(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            level=data.get('level'),
            enrolled_courses=data.get('enrolled_courses', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'active')
        )
