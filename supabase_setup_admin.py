import os
import argparse
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_supabase_admin(email: str, password: str):
    """Create an admin user in Supabase"""
    try:
        # Create user in auth.users table
        user_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True  # Skip email confirmation
        })
        
        if user_response.user:
            user_id = user_response.user.id
            print(f"Created user: {email} with ID: {user_id}")
            
            # Add user to admins table
            admin_response = supabase.table("admins").insert({
                "user_id": user_id,
                "email": email
            }).execute()
            
            if admin_response.data:
                print(f"Added {email} to admins table")
                return True
            else:
                print("Failed to add user to admins table")
                return False
        else:
            print("Failed to create user in auth.users")
            return False
            
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create Supabase admin user')
    parser.add_argument('--email', required=True, help='Admin email address')
    parser.add_argument('--password', required=True, help='Admin password')
    args = parser.parse_args()
    
    success = create_supabase_admin(args.email, args.password)
    if success:
        print("Admin created successfully")
    else:
        print("Failed to create admin")
        sys.exit(1)