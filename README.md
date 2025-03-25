```
# E-Learning Platform

A modern Flask-based e-learning platform with Supabase authentication and PostgreSQL database.

## Features

- 🔐 Secure Authentication with Supabase
- 📊 Comprehensive Admin Dashboard
- 📚 Course Management System
- 👥 Student Management
- 📝 Assignment & Quiz System
- 📈 Progress Tracking
- 🔄 Real-time Updates (via Supabase Realtime, if implemented)
- 🎨 Modern, Responsive UI

## Tech Stack

- **Backend**: Flask (Python 3.12)
- **Authentication**: Supabase Auth
- **Database**: PostgreSQL (via Supabase)
- **Frontend**: Bootstrap 5, DataTables
- **Security**: CSRF Protection, Session Management

## Project Structure
```
app/
├── __init__.py           # Application factory
├── routes/         # API endpoints
│  ├── admin.py     # Admin routes
│  ├── auth.py     # Authentication routes
│  └── courses.py    # Course management routes
├── services/       # Business logic
│  ├── admin_service.py
│  ├── auth_service.py
│  └── courses_service.py
├── middleware/      # Request processing
│  └── auth.py     # Authentication middleware
├── templates/       # HTML templates
│  └── admin/     # Admin interface templates
└── static/       # Static assets
  └── css/      # Stylesheets
```

## Setup Instructions

### Prerequisites
- Python 3.12+
- pip (Python package manager)
- Supabase project

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd elearning_platform
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Unix/MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Supabase Setup:
  - Create a project at [Supabase](https://supabase.com/)
  - Go to Project Settings > API
  - Copy your Supabase URL and anon key.

5. Environment Configuration:
  Create `.env` file in root directory:
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_SECRET_KEY=your-secret-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
```

6. Run the application:
```bash
flask run
```

## API Documentation

### Authentication Endpoints

#### Admin Login
- **POST** `/admin/login`
 - Authenticates admin users via Supabase
 - Returns JWT token on success

#### Token Verification
- **POST** `/admin/verify`
 - Verifies admin authentication token
 - Required for admin dashboard access

### Admin Dashboard Endpoints

#### Dashboard Overview
- **GET** `/admin/dashboard`
 - Returns platform statistics
 - Student count, course metrics, etc.

#### Student Management
- **GET** `/admin/students`
 - Lists all students
 - Supports pagination and search

#### Course Management
- **GET** `/admin/courses`
 - Lists all courses
- **POST** `/admin/courses`
 - Creates new course
- **PUT** `/admin/courses/<id>`
 - Updates course details
- **DELETE** `/admin/courses/<id>`
 - Removes course

### Security

1. **Authentication**
  - Supabase Authentication
  - JWT token validation
  - Role-based access control

2. **Session Security**
  - Secure session cookies
  - CSRF protection
  - HTTP-only cookies

3. **API Security**
  - CORS configuration
  - Rate limiting
  - Input validation

## Development

### Running Tests
```bash
python -m pytest
```

### Code Style
Follow PEP 8 guidelines for Python code.

### Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## Production Deployment

### Requirements
- HTTPS enabled
- Production-grade WSGI server (e.g., Gunicorn)
- Proper firewall configuration
- Regular backups

### Environment Variables
Update for production:
```env
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=True
```

## Support

For support, email support@example.com or create an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```
Key changes made:

* **Replaced Firebase with Supabase:**
    * Authentication: Firebase Auth -> Supabase Auth
    * Database: Firestore -> PostgreSQL (via Supabase)