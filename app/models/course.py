"""Course model for the e-learning platform."""

from datetime import datetime

class Course:
    """Course model class representing a course in the platform."""

    def __init__(self, title, description, instructor_id, price, 
                 created_at=None, updated_at=None, status="active"):
        """
        Initialize a new Course instance.

        Args:
            title (str): Course title
            description (str): Course description
            instructor_id (str): ID of the instructor teaching the course
            price (float): Course price
            created_at (datetime, optional): Creation timestamp. Defaults to current time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current time.
            status (str, optional): Course status. Defaults to "active".
        """
        self.title = title
        self.description = description
        self.instructor_id = instructor_id
        self.price = float(price)
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status = status

    def to_dict(self):
        """
        Convert the Course instance to a dictionary.

        Returns:
            dict: Dictionary representation of the course
        """
        return {
            'title': self.title,
            'description': self.description,
            'instructor_id': self.instructor_id,
            'price': self.price,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        """
        Create a Course instance from a dictionary.

        Args:
            data (dict): Dictionary containing course data

        Returns:
            Course: New Course instance
        """
        return Course(
            title=data.get('title'),
            description=data.get('description'),
            instructor_id=data.get('instructor_id'),
            price=data.get('price'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'active')
        )
