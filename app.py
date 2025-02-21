import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from survey_routes import survey_bp  # Survey blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret in production

USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# New helper for catalog
def load_catalog():
    try:
        with open('survey_catalog.json', 'r') as f:
            catalog_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        catalog_data = {}
    catalog_list = []
    # If the JSON has a key "catalog" with a list, use that;
    # otherwise, assume the file is a dict mapping survey_key -> survey info.
    if "catalog" in catalog_data and isinstance(catalog_data["catalog"], list):
        catalog_list = catalog_data["catalog"]
    else:
        for key, survey in catalog_data.items():
            # Add the key as an id if it isn't already included.
            survey["id"] = key
            catalog_list.append(survey)
    return catalog_list

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Dashboard route updated to include catalog data.
@app.route('/dashboard')
@login_required
def dashboard():
    catalog = load_catalog()
    return render_template('dashboard.html', catalog=catalog)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    session.pop('username', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

# Register the survey blueprint (remains unchanged)
app.register_blueprint(survey_bp, url_prefix='/surveys')

if __name__ == '__main__':
    app.run(debug=True)
