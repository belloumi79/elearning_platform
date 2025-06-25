import os
from dotenv import load_dotenv
from app.services.auth_service import update_user_password

# Load environment variables
load_dotenv()

def reset_admin_password(user_id, new_password):
    """Reset admin password in Supabase"""
    try:
        success = update_user_password(user_id, new_password)
        if success:
            print(f"Password reset successfully for user {user_id}")
        else:
            print("Password reset failed")
    except Exception as e:
        print(f"Error resetting password: {str(e)}")

if __name__ == "__main__":
    user_id = "6655e512-59fd-45ab-ad9b-d2a118a1d3e0"  # From previous verification
    password = "Devdov2025"
    reset_admin_password(user_id, password)