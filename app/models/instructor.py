"""Instructor model for the e-learning platform."""

from datetime import datetime

class Instructor:
    """Instructor model class representing an instructor in the platform."""

    def __init__(self, name, email, phone, bio=None, specialties=None,
                 created_at=None, updated_at=None, status="active"):
        """
        Initialize a new Instructor instance.

        Args:
            name (str): Instructor's full name
            email (str): Instructor's email address
            phone (str): Instructor's phone number
            bio (str, optional): Instructor's biography
            specialties (list, optional): List of instructor's specialties
            created_at (datetime, optional): Creation timestamp. Defaults to current time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current time.
            status (str, optional): Instructor status. Defaults to "active".
        """
        self.name = name
        self.email = email
        self.phone = phone
        self.bio = bio or ""
        self.specialties = specialties or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status = status

    def to_dict(self):
        """
        Convert the Instructor instance to a dictionary.

        Returns:
            dict: Dictionary representation of the instructor
        """
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'bio': self.bio,
            'specialties': self.specialties,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        """
        Create an Instructor instance from a dictionary.

        Args:
            data (dict): Dictionary containing instructor data

        Returns:
            Instructor: New Instructor instance
        """
        return Instructor(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            bio=data.get('bio'),
            specialties=data.get('specialties', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'active')
        )
