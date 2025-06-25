import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Supabase URL and Service Role Key must be set in environment variables")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_auth_user(email):
    """Verify if user exists in auth.users"""
    try:
        # Use the auth admin API to get user by email
        response = supabase.auth.admin.list_users()
        if response:
            users = response.__dict__.get('users', [])
            user = next((u for u in users if u.email == email), None)
            if user:
                print(f"User found in auth.users: {user.id}")
                return True
            else:
                print(f"No user found in auth.users for {email}")
                return False
        else:
            print("Failed to get users from auth")
            return False
    except Exception as e:
        print(f"Error verifying auth user: {str(e)}")
        return False

if __name__ == "__main__":
    email = "coordinateur.atta3aouen@gmail.com"
    verify_auth_user(email)