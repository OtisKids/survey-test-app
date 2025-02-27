import datetime
import json
import os
import logging
from functools import wraps
from typing import Dict, Any, List
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from survey_routes import survey_bp  # Survey blueprint
from dotenv import load_dotenv
from flask_dance.contrib.google import make_google_blueprint, google

# Load environment variables early so they are available for configuration below.
load_dotenv('.env.local')  # Loads variables from .env.local into os.environ

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure app settings using environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_default')
app.config['USERS_FILE'] = os.environ.get('USERS_FILE', 'users.json')
app.config['CATALOG_FILE'] = os.environ.get('CATALOG_FILE', 'survey_catalog.json')

# Allow OAuth over http for testing (DO NOT use in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configure the Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET'),
    scope=[
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_url="/google_register"  # The route where Google will redirect after auth
)
app.register_blueprint(google_bp, url_prefix="/login")

def load_users() -> Dict[str, Any]:
    """
    Load users from the JSON file defined in configuration.
    
    Returns:
        A dictionary of users or an empty dictionary in case of errors.
    """
    try:
        with open(app.config['USERS_FILE'], 'r') as f:
            users = json.load(f)
            return users
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to load users: {e}")
        return {}

def save_users(users: Dict[str, Any]) -> None:
    """
    Save the users dictionary to the JSON file defined in configuration.
    
    Args:
        users: The dictionary containing user data.
    """
    try:
        with open(app.config['USERS_FILE'], 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing the route.
    
    If not logged in, flashes an error and redirects to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_catalog() -> List[Dict[str, Any]]:
    """
    Load the survey catalog from the JSON file defined in configuration.
    
    Handles legacy and new formats. Returns:
        A list of survey dictionaries.
    """
    try:
        with open(app.config['CATALOG_FILE'], 'r') as f:
            catalog_data = json.load(f)
            # If legacy format (a list), convert to new format.
            if isinstance(catalog_data, list):
                catalog_data = {"allowedCategories": [], "surveys": catalog_data}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to load catalog: {e}")
        catalog_data = {"allowedCategories": [], "surveys": []}

    if "surveys" in catalog_data and isinstance(catalog_data["surveys"], list):
        return catalog_data["surveys"]

    # Fallback: Process catalog_data as a dictionary mapping survey_key to survey info.
    catalog_list = []
    for key, survey in catalog_data.items():
        if isinstance(survey, dict):
            # Ensure each survey has an 'id'
            survey.setdefault("id", key)
            catalog_list.append(survey)
    return catalog_list

@app.route('/')
def index():
    """
    Index route. If a user is logged in, redirect to the dashboard.
    Otherwise, render the homepage.
    """
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard route.
    Loads the survey catalog and renders the dashboard template.
    """
    catalog = load_catalog()
    return render_template('dashboard.html', catalog=catalog, current_year='2025' )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    
    GET: Renders the login form.
    POST: Processes the login form, validates the credentials, and logs the user in.
    """
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
    """
    User registration route.
    
    GET: Renders the registration form.
    POST: Processes the registration form, creates a new user, and redirects to login.
    """
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
    """
    Log out route.
    
    Clears the user session and redirects to the login page.
    """
    session.pop('username', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route("/google_register")
def google_register():
    """
    Google registration/login route.
    
    Handles the callback from Google OAuth authorization. 
    If successful, creates a user account or logs in the user.
    """
    # If the user is not yet authenticated with Google, redirect to the Google login page
    if not google.authorized:
        return redirect(url_for("google.login"))
        
    # Get the user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", category="error")
        return redirect(url_for("register"))
    
    user_info = resp.json()
    email = user_info.get("email")
    name = user_info.get("name", email.split('@')[0])  # Use part of email if name not available
    
    # Check if user exists or create a new one
    users = load_users()
    if email in users:
        # User exists, log them in
        session['username'] = email
        flash(f"Logged in successfully with Google as {name}!", "success")
    else:
        # Create a new user with Google credentials
        # We don't need a password since they'll use Google for login
        users[email] = {
            'name': name,
            'email': email,
            'google_auth': True
        }
        save_users(users)
        session['username'] = email
        flash(f"Registered successfully with Google as {name}!", "success")
    
    return redirect(url_for("dashboard"))

@app.route('/user/history')
def user_history():
    # Replace with actual logic to fetch user's completed surveys.
    user_surveys = [
        {'id': 1, 'title': 'Customer Satisfaction Survey'},
        {'id': 2, 'title': 'Product Feedback Survey'}
    ]
    return render_template("user_history.html", surveys=user_surveys)

@app.route('/user/info')
def user_info():
    # Replace with actual logic to fetch user personal information.
    user_info = {'username': session.get('username', 'User'), 'email': 'user@example.com'}
    return render_template("user_info.html", user=user_info)

@app.route('/user/billing')
def user_billing():
    # Replace with actual logic to fetch billing/plans data.
    plans = [
        {'name': 'Free', 'features': 'Basic features'},
        {'name': 'Premium', 'features': 'Advanced features and priority support'}
    ]
    return render_template("user_billing.html", plans=plans)

# Register the survey blueprint under the '/surveys' URL prefix.
app.register_blueprint(survey_bp, url_prefix='/surveys')

if __name__ == '__main__':
    # Debug mode should be disabled in production
    app.run(debug=True)
