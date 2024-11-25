"""Models package for the e-learning platform."""

from app.models.user import User
from app.models.course import Course
from app.models.student import Student
from app.models.instructor import Instructor

__all__ = ['User', 'Course', 'Student', 'Instructor']
