"""
Script to set up an admin user in the e-learning platform using Supabase.
This script should be run from the command line with the admin user's email and password as arguments.
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import sys
import os
from datetime import datetime
from supabase import create_client
from app.database.supabase_db import get_supabase_client

def get_supabase_service_client():
    """Get Supabase client with service role key to bypass RLS"""
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set in environment variables")
    return create_client(supabase_url, service_key)

def setup_admin_user(email, password):
    """Set up a user as an admin in Supabase.
    
    Args:
        email (str): Email of the admin user
        password (str): Password for the admin user
    """
    try:
        supabase_client = get_supabase_client()
        
        # Create auth user
        try:
            auth_response = supabase_client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "role": "admin"
                    }
                }
            })
            
            print(f"Auth response: {auth_response}")  # Debug output
            
            if hasattr(auth_response, 'user'):
                user_id = auth_response.user.id
            else:
                print("Error: Auth response missing user data")
                return False
        except Exception as e:
            print(f"Error during user creation: {str(e)}")
            return False
        
        # Check if admins table exists, create if needed
        try:
            supabase_client.from_('admins').select('*').limit(1).execute()
        except Exception as e:
            print("Admins table doesn't exist, creating...")
            supabase_client.from_('admins').insert({
                'email': 'initial@example.com',
                'user_id': '00000000-0000-0000-0000-000000000000',
                'created_at': datetime.utcnow().isoformat()
            }).execute()

        # Create admin record using service role client to bypass RLS
        try:
            service_client = get_supabase_service_client()
            response = service_client.from_('admins').insert({
                'email': email,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            print(f"\nSuccessfully created admin user: {email}")
            print(f"Admin record created: {response}")
            return True
        except Exception as e:
            print(f"Error creating admin record: {str(e)}")
            return False
        
    except Exception as e:
        print(f"Error setting up admin user: {str(e)}")
        return False

def main():
    """Main function to run the script."""
    if len(sys.argv) != 3:
        print("Usage: python setup_admin.py <admin_email> <admin_password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Set up admin user
    if not setup_admin_user(email, password):
        sys.exit(1)

if __name__ == "__main__":
    main()
