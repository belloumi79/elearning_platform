import sys
import os

# Ajoutez le chemin de votre application
path = '/home/belloumi79/elearning_platform'
if path not in sys.path:
    sys.path.append(path)

# Configuration des variables d'environnement
os.environ['FLASK_APP'] = 'run.py'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'
os.environ['FLASK_SECRET_KEY'] = 'your_secure_secret_key_here_replace_in_production'

# Firebase Web Configuration
os.environ['FIREBASE_API_KEY'] = 'AIzaSyC0U958fXyh7NkVMT8xiXGFYViWpdyY4gM'
os.environ['FIREBASE_AUTH_DOMAIN'] = 'iqrawartaki-af01c.firebaseapp.com'
os.environ['FIREBASE_PROJECT_ID'] = 'iqrawartaki-af01c'
os.environ['FIREBASE_STORAGE_BUCKET'] = 'iqrawartaki-af01c.firebasestorage.app'
os.environ['FIREBASE_MESSAGING_SENDER_ID'] = '434590337288'
os.environ['FIREBASE_APP_ID'] = '1:434590337288:web:af76e8501a93d54fed44bd'
os.environ['FIREBASE_MEASUREMENT_ID'] = 'G-7Z32Z17QRB'

# Firebase Admin SDK Configuration
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/belloumi79/elearning_platform/config/serviceAccountKey.json'

# Import l'application depuis run.py
from run import app as application

if __name__ == '__main__':
    application.run()
