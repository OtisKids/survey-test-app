import json
import os
import logging
from functools import wraps
from typing import Dict, Any, List
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from survey_routes import survey_bp  # Survey blueprint
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use env variable in production

# Configuration for file paths
load_dotenv('.env.local')  # Or just load_dotenv() to automatically find a .env file

app.secret_key = os.environ.get('SECRET_KEY', 'fallback_default')
USERS_FILE = os.environ.get('USERS_FILE', 'users.json')
CATALOG_FILE = os.environ.get('CATALOG_FILE', 'survey_catalog.json')

def load_users() -> Dict[str, Any]:
    """Load users from the JSON file."""
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            return users
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to load users: {e}")
        return {}

def save_users(users: Dict[str, Any]) -> None:
    """Save the users dictionary to the JSON file."""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def login_required(f):
    """Decorator to ensure a user is logged in before accessing particular routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_catalog() -> List[Dict[str, Any]]:
    """Load the survey catalog from a JSON file and return a list of surveys."""
    try:
        with open(CATALOG_FILE, 'r') as f:
            catalog_data = json.load(f)
            # If legacy format (a list), convert it.
            if isinstance(catalog_data, list):
                catalog_data = {"allowedCategories": [], "surveys": catalog_data}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to load catalog: {e}")
        catalog_data = {"allowedCategories": [], "surveys": []}

    # Now, if the catalog is in its new format, simply return the surveys.
    if "surveys" in catalog_data and isinstance(catalog_data["surveys"], list):
        return catalog_data["surveys"]

    # Otherwise, assume catalog_data maps survey_key -> survey info.
    catalog_list = []
    for key, survey in catalog_data.items():
        # Only process items where survey is a dictionary.
        if isinstance(survey, dict):
            survey.setdefault("id", key)
            catalog_list.append(survey)
    return catalog_list



@app.route('/')
def index():
    """Index route. Redirects logged-in users to the dashboard."""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route that loads survey catalog data."""
    catalog = load_catalog()
    return render_template('dashboard.html', catalog=catalog)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login. Renders login form on GET and processes login on POST."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        users = load_users()
        if username in users:
            stored_hash = users[username]['password']
            if check_password_hash(stored_hash, password):
                session['username'] = username
                flash("Logged in successfully!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("User not found.", "error")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration. Renders registration form on GET and processes registration on POST."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        users = load_users()
        if username in users:
            flash("Username already exists.", "error")
            return redirect(url_for('register'))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        users[username] = {'password': hashed}
        save_users(users)
        flash("Registered successfully. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Log out route. Clears the session and redirects to login."""
    session.pop('username', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

# Register the survey blueprint under the /surveys URL prefix.
app.register_blueprint(survey_bp, url_prefix='/surveys')

if __name__ == '__main__':
    app.run(debug=True)
