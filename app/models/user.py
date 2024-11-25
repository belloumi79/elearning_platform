"""User model for the e-learning platform."""

from datetime import datetime

class User:
    """User model class representing a user in the platform."""

    def __init__(self, email, name, role="user", created_at=None, 
                 updated_at=None, status="active", uid=None):
        """
        Initialize a new User instance.

        Args:
            email (str): User's email address
            name (str): User's full name
            role (str, optional): User's role. Defaults to "user".
            created_at (datetime, optional): Creation timestamp. Defaults to current time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current time.
            status (str, optional): User status. Defaults to "active".
            uid (str, optional): Firebase user ID. Defaults to None.
        """
        self.email = email
        self.name = name
        self.role = role
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status = status
        self.uid = uid

    def to_dict(self):
        """
        Convert the User instance to a dictionary.

        Returns:
            dict: Dictionary representation of the user
        """
        return {
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'uid': self.uid
        }

    @staticmethod
    def from_dict(data):
        """
        Create a User instance from a dictionary.

        Args:
            data (dict): Dictionary containing user data

        Returns:
            User: New User instance
        """
        return User(
            email=data.get('email'),
            name=data.get('name'),
            role=data.get('role', 'user'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'active'),
            uid=data.get('uid')
        )
