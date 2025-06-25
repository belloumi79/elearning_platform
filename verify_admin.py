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

def verify_admin(email):
    """Verify if admin exists in Supabase"""
    try:
        res = supabase.table("admins").select("*").eq("email", email).execute()
        if res.data and len(res.data) > 0:
            print(f"Admin record found for {email}:")
            print(res.data[0])
            return True
        else:
            print(f"No admin record found for {email}")
            return False
    except Exception as e:
        print(f"Error verifying admin: {str(e)}")
        return False

if __name__ == "__main__":
    email = "coordinateur.atta3aouen@gmail.com"
    verify_admin(email)