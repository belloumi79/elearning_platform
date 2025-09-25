import sys
import os

# Minimal WSGI entrypoint for Flask app (Supabase backend)
# Adjust project path if deploying under a different directory structure.
project_path = os.getenv('APP_PATH', os.getcwd())
if project_path not in sys.path:
    sys.path.append(project_path)

# Basic Flask environment
os.environ.setdefault('FLASK_APP', 'run.py')
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

# Import the application from run.py
from run import app as application

if __name__ == '__main__':
    application.run()
