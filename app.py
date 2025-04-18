import os
from dotenv import load_dotenv
import logging
from flask import Flask, redirect, url_for
from extentions import db
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///network_incidents.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # Initialize extensions
    from extentions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate = Migrate(app, db)
    # Import models
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth import auth_bp
    from incident import incident_bp
    from analysis import analysis_bp
    from api import api_bp
 

    app.register_blueprint(auth_bp)
    app.register_blueprint(incident_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    #app.register_blueprint(kb_bp)

    @app.route('/')
    def home():
        return redirect(url_for('incident.dashboard'))

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from extentions import db
        from models import init_data
        db.create_all()
        init_data()
        
    
    app.run(host='0.0.0.0', port=5000, debug=True)