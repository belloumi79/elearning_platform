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

def reset_admin_password(user_id, new_password):
    """Reset admin password in Supabase"""
    try:
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        if response.user:
            print(f"Password reset successfully for user {user_id}")
            return True
        else:
            error = response.error.message if response.error else "Unknown error"
            print(f"Password reset failed: {error}")
            return False
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        return False

if __name__ == "__main__":
    user_id = "6655e512-59fd-45ab-ad9b-d2a118a1d3e0"  # From previous verification
    password = "Devdov2025"
    reset_admin_password(user_id, password)