import logging
from logging.handlers import RotatingFileHandler
import os

def init_logging():
    """Initialize logging configuration"""
    # Create logs directory if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Main application logger
    logger = logging.getLogger('elearning')
    logger.setLevel(logging.DEBUG)
    
    # File handler (rotating logs)
    file_handler = RotatingFileHandler(
        'logs/flask.log',
        maxBytes=1024 * 1024,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    logger.addHandler(console_handler)
