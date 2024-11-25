"""
Development configuration settings for the e-learning platform.

This module contains configuration settings specific to the development
environment. It includes database URIs, API keys, and other environment-specific
variables.
"""

import os
from datetime import timedelta

# Flask Configuration
DEBUG = True
TESTING = False
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Session Configuration
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = 'flask_session'
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Protection
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', 'csrf-secret-key-change-in-production')

# Firebase Configuration
FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}

# Firestore Configuration
FIRESTORE_KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'serviceAccountKey.json')

# Security Headers
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://www.gstatic.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com;"
}

# CORS Configuration
CORS_ORIGINS = [
    'http://localhost:5000',
    'http://127.0.0.1:5000'
]

# File Upload Configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# Cache Configuration
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300

# Rate Limiting
RATELIMIT_DEFAULT = "200 per day;50 per hour"
RATELIMIT_STORAGE_URL = "memory://"

# Development-specific Logging
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'logs/development.log'

# Email Configuration (for development)
MAIL_SERVER = 'smtp.mailtrap.io'
MAIL_PORT = 2525
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_USE_TLS = True
MAIL_USE_SSL = False
