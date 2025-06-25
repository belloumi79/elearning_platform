import os
from supabase import create_client, Client
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client using Service Role Key
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("Supabase client initialized with Service Role Key.")

def update_user_password(user_id: str, new_password: str):
    """
    Updates a user's password using Supabase's admin API.
    
    Args:
        user_id (str): The ID of the user whose password needs to be updated.
        new_password (str): The new password for the user.
        
    Raises:
        Exception: If the password update fails.
    """
    try:
        logger.info(f"Attempting to update password for user ID: {user_id}")
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )
        if response.user:
            logger.info(f"Password updated successfully for user ID: {user_id}")
            return True
        else:
            error_message = "Unknown error during password update."
            if hasattr(response, 'error') and response.error:
                error_message = response.error.message
            logger.error(f"Failed to update password for user ID {user_id}: {error_message}")
            raise Exception(f"Failed to update password: {error_message}")
    except Exception as e:
        logger.error(f"Error updating password for user ID {user_id}: {str(e)}")
        raise Exception(f"Error updating password: {str(e)}")

if __name__ == "__main__":
    # Option 1: Reset password for existing user (belloumi.karim.professional@gmail.com)
    # user_id_to_reset = "d619ecfb-465e-4f60-9330-f37e74ba257f"
    # new_password = "Devdov2025"
    
    # try:
    #     update_user_password(user_id_to_reset, new_password)
    #     print(f"Password for user ID {user_id_to_reset} successfully updated.")
    # except Exception as e:
    #     print(f"Failed to update password: {e}")

    # Option 2: Create a new admin user (temp.admin.elearning@gmail.com)
    temp_admin_email = "temp.admin.elearning@gmail.com"
    temp_admin_password = "Devdov2025"

    try:
        logger.info(f"Attempting to create new admin user: {temp_admin_email}")
        create_response = supabase.auth.admin.create_user(
            {
                "email": temp_admin_email,
                "password": temp_admin_password,
                "email_confirm": True # Set to True to require email confirmation, False to bypass
            }
        )
        
        if create_response.user:
            user_id = create_response.user.id
            logger.info(f"User {temp_admin_email} created successfully with ID: {user_id}")

            # Set user role to 'admin' in auth.users table
            update_role_response = supabase.from_('auth.users').update({'role': 'admin'}).eq('id', user_id).execute()
            if update_role_response.error:
                logger.warning(f"Failed to set role to 'admin' for user ID {user_id}: {update_role_response.error.message}")
            else:
                logger.info(f"Role set to 'admin' for user ID: {user_id}.")

            # Ensure the user is in the public.admins table
            logger.info(f"Ensuring user {user_id} ({temp_admin_email}) is in public.admins table.")
            admin_check_response = supabase.from_('admins').select("user_id").eq('user_id', user_id).limit(1).execute()
            if not admin_check_response.data:
                insert_data = {"user_id": user_id, "email": temp_admin_email}
                insert_response = supabase.from_('admins').insert(insert_data).execute()
                if insert_response.error:
                    raise Exception(f"Failed to insert into public.admins: {insert_response.error.message}")
                logger.info(f"User {temp_admin_email} (ID: {user_id}) successfully added to public.admins.")
            else:
                logger.info(f"User {temp_admin_email} (ID: {user_id}) already exists in public.admins.")

            print(f"New admin user '{temp_admin_email}' created and configured with password '{temp_admin_password}'.")
            print("Please note: If 'email_confirm' was set to True, the user might need to confirm their email before logging in.")
        else:
            error_message = "Unknown error during user creation."
            if hasattr(create_response, 'error') and create_response.error:
                error_message = create_response.error.message
            raise Exception(f"Failed to create user: {error_message}")

    except Exception as e:
        print(f"Failed to create/ensure admin user: {e}")