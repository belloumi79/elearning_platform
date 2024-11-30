import firebase_admin
from firebase_admin import credentials
from firebase_functions import https_fn
from flask import Flask, request
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Firebase Admin with your credentials
cred = credentials.Certificate('../config/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Import your existing Flask app
from run import app

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function that wraps a Flask app."""
    with app.request_context(req.environ):
        return app.full_dispatch_request()
