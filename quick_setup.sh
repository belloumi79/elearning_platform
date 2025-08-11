#!/bin/bash

# Quick setup script for the e-learning platform
# This script installs dependencies using --break-system-packages as a workaround

echo "Quick setup for E-learning Platform..."

# Install required packages using --break-system-packages
pip install python-dotenv==1.0.0 flask==3.0.2 flask-cors==3.0.10 supabase>=2.14.0 python-multipart==0.0.3 passlib==1.7.4 python-dateutil==2.8.2 psycopg2-binary==2.9.9 gunicorn==21.2.0 Flask-Session Flask-Login flask-migrate flask-bcrypt flask-mail redis==5.0.1 --break-system-packages

echo "Dependencies installed successfully!"
echo "You can now run the application with:"
echo "  python run.py"