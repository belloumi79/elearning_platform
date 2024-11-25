"""
Script to set up an admin user in the e-learning platform.
This script should be run from the command line with the admin user's email as an argument.
"""

import firebase_admin
from firebase_admin import auth, credentials, firestore
import sys
import os
from datetime import datetime

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Get the absolute path to the service account key
        cred_path = os.path.join(os.path.dirname(__file__), 'config', 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return False

def setup_admin_user(email):
    """Set up a user as an admin.
    
    Args:
        email (str): Email of the user to make admin
    """
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        print(f"Found user: {user.uid}")
        
        # Set admin custom claim
        auth.set_custom_user_claims(user.uid, {'admin': True})
        print(f"Set admin claim for user: {user.uid}")
        
        # Create admin document in Firestore
        db = firestore.client()
        admin_ref = db.collection('admins').document(user.uid)
        admin_ref.set({
            'email': email,
            'created_at': datetime.utcnow(),
            'uid': user.uid
        })
        print(f"Created admin document for user: {user.uid}")
        
        print(f"\nSuccessfully set up admin user: {email}")
        return True
        
    except auth.UserNotFoundError:
        print(f"Error: User with email {email} not found")
        return False
    except Exception as e:
        print(f"Error setting up admin user: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    if len(sys.argv) != 2:
        print("Usage: python setup_admin.py <admin_email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Set up admin user
    if not setup_admin_user(email):
        sys.exit(1)

if __name__ == "__main__":
    main()
