"""Firestore database configuration for the e-learning platform."""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import logging
import json
from google.api_core import exceptions

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_credentials_path():
    """Get the absolute path to the service account credentials file."""
    # First try environment variable
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path and os.path.exists(cred_path):
        return os.path.abspath(cred_path)
    
    # Then try default location
    default_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config',
        'serviceAccountKey.json'
    ))
    if os.path.exists(default_path):
        return default_path
    
    raise FileNotFoundError("Service account credentials file not found")

def validate_credentials(cred_path):
    """Validate the service account credentials file."""
    try:
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in cred_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields in credentials file: {', '.join(missing_fields)}")
        
        if cred_data['type'] != 'service_account':
            raise ValueError("Invalid credential type. Must be 'service_account'")
        
        return cred_data
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in credentials file")

def initialize_firestore():
    """
    Initialize Firestore client with proper error handling and validation.
    
    Returns:
        firestore.Client: Initialized Firestore client
    
    Raises:
        Exception: If initialization fails
    """
    try:
        # Get and validate credentials
        cred_path = get_credentials_path()
        cred_data = validate_credentials(cred_path)
        
        logger.info(f"Initializing Firebase Admin SDK with credentials from: {cred_path}")
        logger.info(f"Using service account: {cred_data.get('client_email')}")
        
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        
        # Get Firestore client
        db = firestore.client()
        
        # Test the connection with a simple operation
        try:
            # Try to list collections (requires minimal permissions)
            list(db.collections())
            logger.info("Firestore connection test successful")
            return db
        except exceptions.PermissionDenied as e:
            error_msg = ("Insufficient permissions. Please ensure the service account "
                        "has the following roles in Firebase Console:\n"
                        "1. Firebase Admin SDK Administrator Service Agent\n"
                        "2. Cloud Datastore User\n"
                        "3. Service Account Token Creator")
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            logger.error(f"Firestore connection test failed: {str(e)}")
            raise
    
    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {str(e)}")
        raise

# Initialize Firestore client
db = None
try:
    db = initialize_firestore()
except Exception as e:
    logger.error(f"Error initializing Firestore: {str(e)}")
    # Don't raise here - let the application handle the uninitialized db gracefully
