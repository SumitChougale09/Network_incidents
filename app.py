import os
import logging
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQL Alchemy models
class Base(DeclarativeBase):
    pass

# Create SQLAlchemy extension
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Create tables and import models within app context
with app.app_context():
    # Import models after db initialization to avoid circular imports
    from models import User, init_data
    db.create_all()

# Import routes after app initialization to avoid circular imports
from auth import auth_bp
from incident import incident_bp
from analysis import analysis_bp
from api import api_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Load user from user_id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('incident.dashboard'))

# Initialize sample data for the database if empty
with app.app_context():
    init_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
