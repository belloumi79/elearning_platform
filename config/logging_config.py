import logging
from logging.handlers import RotatingFileHandler
import os

def init_logging():
    """Initialize logging configuration"""
    # Create logs directory if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure the root logger
    logger = logging.getLogger() # Get the root logger
    logger.setLevel(logging.DEBUG) # Set root logger level to DEBUG

    # Prevent adding handlers multiple times if init_logging is called again
    if logger.hasHandlers():
        logger.handlers.clear()

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
    console_handler.setLevel(logging.INFO) # Keep console less verbose
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s' # Added timestamp to console
    ))
    logger.addHandler(console_handler)
