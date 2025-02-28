# blueprints/auth/routes.py
import os
from flask import render_template, redirect, url_for, request, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.security import generate_password_hash, check_password_hash
from helpers.auth_helpers import validate_login, validate_registration
from helpers.survey_helpers import load_users, save_users
from blueprints.auth import auth_bp

# Configure the Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    scope=[
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="auth.google_callback"
)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Check if user is already logged in
    if 'username' in session:
        flash('You are already logged in', 'info')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('username', '').lower().strip()
        password = request.form.get('password', '')
        
        # Validate inputs
        
        if not validate_login(email, password):
            flash('Please enter a valid email and password', 'error')
            return render_template('login.html')
        
        # Check credentials
        users = load_users()
        print(f'users are', users)
        if email in users and check_password_hash(users[email].get('password', ''), password):
            session['username'] = email
            flash('Login successful', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    # Check if user is already logged in
    if 'username' in session:
        flash('You are already logged in', 'info')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('username', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate inputs
        if not validate_registration(name, email, password, confirm_password):
            return render_template('register.html')
        
        # Check if user already exists
        users = load_users()
        if email in users:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        users[email] = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'google_auth': False
        }
        save_users(users)
        
        # Auto login
        session['username'] = email
        flash('Registration successful', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('register.html')

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login"""
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect(url_for('auth.google_callback'))

@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    if not google.authorized:
        flash('Google authentication failed', 'error')
        return redirect(url_for('auth.login'))
    
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Failed to get user info from Google', 'error')
        return redirect(url_for('auth.login'))
    
    user_info = resp.json()
    email = user_info.get('email')
    name = user_info.get('name', email.split('@')[0])
    
    # Check if user exists
    users = load_users()
    if email in users:
        # User exists, log them in
        session['username'] = email
        flash(f'Welcome back, {name}!', 'success')
    else:
        # Create new user with Google credentials
        users[email] = {
            'name': name,
            'email': email,
            'google_auth': True
        }
        save_users(users)
        session['username'] = email
        flash(f'Account created successfully, {name}!', 'success')
    
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))