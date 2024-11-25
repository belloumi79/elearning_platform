"""
Logging configuration for the e-learning platform.

This module provides a comprehensive logging setup with different handlers
and formatters for various logging needs. It includes configurations for:
- Console logging
- File logging
- Error logging
- Access logging
"""

import os
import logging.config
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file paths
APP_LOG = os.path.join(LOGS_DIR, 'app.log')
ERROR_LOG = os.path.join(LOGS_DIR, 'error.log')
ACCESS_LOG = os.path.join(LOGS_DIR, 'access.log')
SECURITY_LOG = os.path.join(LOGS_DIR, 'security.log')

# Logging configuration dictionary
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'access': {
            'format': '%(asctime)s - %(remote_addr)s - %(username)s - %(request_method)s %(request_path)s - %(status)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': APP_LOG,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': ERROR_LOG,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'access_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'formatter': 'access',
            'filename': ACCESS_LOG,
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'encoding': 'utf8'
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': SECURITY_LOG,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
    },
    
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'app_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'app': {  # Application logger
            'handlers': ['app_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'access': {  # Access logger
            'handlers': ['access_file'],
            'level': 'INFO',
            'propagate': False
        },
        'security': {  # Security logger
            'handlers': ['security_file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

def init_logging():
    """Initialize logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Create a logger instance for the application
    logger = logging.getLogger('app')
    logger.info('Logging system initialized')
