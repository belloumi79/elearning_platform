import firebase_admin
from firebase_admin import credentials, auth, firestore
import sys
import os

def setup_admin(email):
    try:
        # Initialize Firebase Admin SDK
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        cred = credentials.Certificate(os.path.join(root_dir, "config", "serviceAccountKey.json"))
        firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        db = firestore.client()
        
        # Try to get user by email
        try:
            user = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            print(f"User with email {email} not found. Please create an account first.")
            return
        
        # Set custom claims
        auth.set_custom_user_claims(user.uid, {'admin': True})
        
        # Update or create user document in Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email': email,
            'isAdmin': True,
            'role': 'admin'
        }, merge=True)
        
        print(f"Successfully set up admin privileges for user: {email}")
        
    except Exception as e:
        print(f"Error setting up admin: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python setup_admin.py <admin_email>")
        sys.exit(1)
    
    admin_email = sys.argv[1]
    setup_admin(admin_email)
