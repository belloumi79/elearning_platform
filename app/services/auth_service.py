"""
Authentication service module for the e-learning platform.

This module handles Firebase token verification and admin status checking.
It interacts with Firebase Authentication and Firestore to validate user
credentials and retrieve user data.

Functions:
    verify_admin_token: Verify Firebase ID token and check admin status

Dependencies:
    - firebase_admin.auth: For token verification
    - firebase_admin.firestore: For user data retrieval
"""

from firebase_admin import auth, firestore
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
db = firestore.client()

def verify_admin_token(id_token):
    """Verify Firebase ID token and check admin status.
    
    This function performs several checks:
    1. Validates the Firebase ID token
    2. Checks if the token is revoked
    3. Verifies user existence and admin status
    
    Args:
        id_token (str): Firebase ID token to verify
        
    Returns:
        dict: User data containing:
            - uid (str): User ID
            - email (str): User email
            - name (str): User display name
            - isAdmin (bool): Admin status
            
    Raises:
        ValueError: If token is invalid or user is not an admin
        auth.InvalidIdTokenError: If token verification fails
        Exception: For other unexpected errors
    """
    try:
        logger.info("Starting token verification process...")
        logger.debug(f"Received token: {id_token[:10]}...")
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        logger.info(f"Token verified successfully. Claims: {decoded_token.get('claims', {})}")
        
        # Get user from Firebase Auth
        uid = decoded_token['uid']
        user = auth.get_user(uid)
        logger.info(f"Retrieved user data - Email: {user.email}, UID: {uid}")
        
        # First, check custom claims
        custom_claims = decoded_token.get('claims', {})
        logger.info(f"Custom claims from token: {custom_claims}")
        
        if custom_claims.get('admin', False):
            logger.info(f"User {uid} verified as admin through custom claims")
            return {
                'uid': uid,
                'email': user.email,
                'name': user.display_name,
                'isAdmin': True
            }
            
        # If no admin claim, check if user exists in admins collection
        try:
            admin_ref = db.collection('admins').document(uid)
            admin_doc = admin_ref.get()
            
            if admin_doc.exists:
                logger.info(f"User {uid} verified as admin through admins collection")
                # Set admin claim for future use
                auth.set_custom_user_claims(uid, {'admin': True})
                return {
                    'uid': uid,
                    'email': user.email,
                    'name': user.display_name,
                    'isAdmin': True
                }
            else:
                logger.warning(f"User {uid} not found in admins collection")
        except Exception as e:
            logger.error(f"Error checking admin status in Firestore: {str(e)}")
        
        # If we get here, user is not an admin
        logger.warning(f"User {uid} attempted admin access but is not authorized")
        raise ValueError("User is not authorized as admin")
        
    except auth.InvalidIdTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise

def create_admin_user(email):
    """
    Create or verify an admin user in Firestore.
    This should be run once to set up the initial admin.
    """
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Set admin custom claim
        auth.set_custom_user_claims(user.uid, {'admin': True})
        
        # Create admin document in Firestore
        admin_ref = db.collection('admins').document(user.uid)
        admin_ref.set({
            'email': email,
            'created_at': datetime.utcnow(),
            'uid': user.uid
        })
        
        logger.info(f"Successfully created admin user for {email}")
        return True
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise
