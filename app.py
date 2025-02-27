# app.py - Main Flask application file
import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, session
from dotenv import load_dotenv

# Load environment variables early
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Application factory function to create and configure the Flask app"""
    app = Flask(__name__)
    
    # Configure app settings
    if test_config is None:
        # Load the configuration from environment variables
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
        if not app.config['SECRET_KEY']:
            logger.warning("No SECRET_KEY set. Using an insecure fallback (not recommended for production).")
            app.config['SECRET_KEY'] = 'fallback_default_do_not_use_in_production'
        
        app.config['USERS_FILE'] = os.environ.get('USERS_FILE', 'users.json')
        app.config['CATALOG_FILE'] = os.environ.get('CATALOG_FILE', 'survey_catalog.json')
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Only enable this for development
    if app.config.get('FLASK_ENV') == 'development':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Register blueprints
    from survey_routes import survey_bp
    from user.routes import user_bp
    from dashboard.routes import dashboard_bp
    from auth.google_auth import google_bp
    
    app.register_blueprint(survey_bp, url_prefix='/surveys')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(google_bp, url_prefix="/login")
    
    # Root route
    @app.route('/')
    def index():
        """Index route with conditional redirect to dashboard"""
        if 'username' in session:
            return redirect(url_for('dashboard_bp.dashboard'))
        return render_template('index.html')
    
    return app

# Only run the application if this script is executed directly
if __name__ == '__main__':
    app = create_app()
    # Check if we're in development mode
    is_development = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=is_development)