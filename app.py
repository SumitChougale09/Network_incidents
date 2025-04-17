import os
import logging
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import routes after app initialization to avoid circular imports
from auth import auth_bp
from incident import incident_bp
from analysis import analysis_bp
from api import api_bp
from models import User, init_data

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Load user from user_id
@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('incident.dashboard'))

# Initialize sample data for the in-memory storage
init_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
