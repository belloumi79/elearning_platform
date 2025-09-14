import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import timedelta
from flask_swagger_ui import get_swaggerui_blueprint
import os
import secrets
from dotenv import load_dotenv
# Removed: import firebase_admin
# Removed: from firebase_admin import credentials
from flask import redirect, url_for

def create_app(config_name=None):
    # Initialize Flask app
    app = Flask(__name__, static_folder='static')

    # Load environment variables
    load_dotenv()

    # Configure secret key
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

    # Remplacez les origines ci‑dessous par votre(s) domaine(s) frontend exact(s).
    # N'utilisez PAS '*' si vous activez supports_credentials=True.
    allowed_origins = [
        "https://elearning-platform-7l0x.onrender.com",        # production frontend (Render)
        "http://localhost:5173",                              # Vite dev
        "https://9000-monospace-iqrawartqui-academy-...cloudworkstations.dev"  # votre dev host exact si nécessaire
        "https://9000-monospace-iqrawartqui-academy-1712137068075.cluster-nxnw2gov3naqkvuxb437f67u5e.cloudworkstations.dev)."
    ]

    CORS(
        app,
        resources={r"/api/v1/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "Accept"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )

    # Ensure preflight requests are handled early and not redirected by auth middleware
    @app.before_request
    def handle_options_and_bypass_auth_for_preflight():
        # If a browser sends an OPTIONS preflight, return 204 directly
        if request.method == 'OPTIONS':
            # Flask-CORS will add the appropriate Access-Control-Allow-* headers
            return "", 204

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

    # Register API blueprints
    from app.routes.auth import auth_bp as auth_api_bp
    from app.routes.admin import admin_bp as admin_api_bp
    from app.routes.student import student_bp as student_api_bp
    from app.routes.courses import courses_bp as courses_api_bp

    app.register_blueprint(auth_api_bp)
    app.register_blueprint(admin_api_bp)
    app.register_blueprint(student_api_bp)
    app.register_blueprint(courses_api_bp)

    # --- Swagger UI Setup ---
    SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
    API_URL = '/static/swagger.json'  # Our API definition

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "E-Learning Platform API"
        }
    )
    app.register_blueprint(swaggerui_blueprint)
    # --- End Swagger UI Setup ---

    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the e-learning platform API. See /api/docs for documentation."})

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'ALLOWALL'
        return response

    return app
