import logging
from flask import Flask
from app.routes.assignments import admin_assignments_bp
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta
import os
import secrets
from dotenv import load_dotenv
# Removed: import firebase_admin
# Removed: from firebase_admin import credentials
from flask import redirect, url_for

def create_app(config_name=None):
    # Initialize Flask app
    app = Flask(__name__, static_folder='app/static')

    # Load environment variables
    load_dotenv()

    # Configure secret key
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'flask_session')
    app.config['SESSION_COOKIE_NAME'] = 'elearning_session'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Removed Firebase config block

    # Initialize extensions
    Session(app)

    # Configure CORS
    CORS(app, resources={
        "r/api/*": {
            "origins": ["https://web-production-8de28.up.railway.app", "http://localhost:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        },
        "r/api/user/*": {
            "origins": ["http://localhost:5000", "https://web-production-8de28.up.railway.app"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        },
        "r/courses/api/*": {
            "origins": ["http://localhost:5000", "https://web-production-8de28.up.railway.app"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })

    # Configure logging
    from config.logging_config import init_logging
    init_logging()
    logger = logging.getLogger(__name__)

    # Clean up test files on startup
    with app.app_context():
        try:
            from app.database.supabase_db import get_supabase_client
            supabase = get_supabase_client()
            # List and remove any test files
            test_files = supabase.storage.from_('assignments').list()
            for file in test_files:
                if file['name'].startswith('test-'):
                    supabase.storage.from_('assignments').remove([file['name']])
            logger.info("Cleaned up test files on startup")
        except Exception as e:
            logger.warning(f"Could not clean test files: {str(e)}")

    # Removed Firebase Admin SDK initialization block

    # Handle favicon requests
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.ico') if os.path.exists(os.path.join(app.static_folder, 'favicon.ico')) else ('', 204)

    # Register blueprints
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.courses import courses_bp
    from app.routes.assignments import assignments_bp
    from app.routes.student import student_bp
    from flask import Blueprint

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_assignments_bp)

    # Create a static blueprint
    static_bp = Blueprint('static', __name__, static_folder='app/static', static_url_path='/static')
    app.register_blueprint(static_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.admin_login'))

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'ALLOWALL'
        return response

    return app
