# setup_admin.py

import os
import sys
import argparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_password'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)
mail = Mail(app)
CORS(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin(email, password):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username='admin', email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    print(f'Admin user created with email: {email}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup admin user')
    parser.add_argument('--email', required=True, help='Admin email address')
    parser.add_argument('--password', required=True, help='Admin password')
    args = parser.parse_args()

    with app.app_context():
        db.create_all()
        create_admin(args.email, args.password)
