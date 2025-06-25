import os
import sys
from dotenv import load_dotenv

# Load environment variables BEFORE importing any app modules
load_dotenv()

# Add app directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth_service import supabase_admin_login

# Test admin login
try:
    email = "coordinateur.atta3aouen@gmail.com"
    password = "Devdov2025"
    result = supabase_admin_login(email, password)
    print("Login successful:")
    print(result)
except Exception as e:
    print(f"Login failed: {str(e)}")