# blueprints/user/routes.py
import logging
from flask import render_template, redirect, url_for, session, flash, request
from helpers.survey_helpers import load_users, save_users, load_responses
from blueprints.user import user_bp
from functools import wraps

logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        username = session.get('username')
        users = load_users()
        user_info = users.get(username, {})
        
        return render_template('user_info.html', user=user_info)
    except Exception as e:
        logger.error(f"Error loading user profile: {str(e)}")
        flash("Error loading profile data", "error")
        return redirect(url_for('dashboard.index'))

@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        username = session.get('username')
        users = load_users()
        
        if username not in users:
            flash("User not found", "error")
            return redirect(url_for('user.profile'))
        
        # Update fields
        name = request.form.get('name', '').strip()
        if name:
            users[username]['name'] = name
            
        # Add other fields as needed
        
        save_users(users)
        flash("Profile updated successfully", "success")
        return redirect(url_for('user.profile'))
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        flash("Error updating profile", "error")
        return redirect(url_for('user.profile'))

@user_bp.route('/history')
@login_required
def history():
    """View user's survey history"""
    try:
        username = session.get('username')
        responses = load_responses()
        
        # Filter responses for this user
        user_responses = [r for r in responses if r.get('username') == username]
        
        return render_template('user_history.html', responses=user_responses)
    except Exception as e:
        logger.error(f"Error loading user history: {str(e)}")
        flash("Error loading history data", "error")
        return redirect(url_for('dashboard.index'))

@user_bp.route('/billing')
@login_required
def billing():
    """User billing page"""
    try:
        username = session.get('username')
        users = load_users()
        user_info = users.get(username, {})
        
        # Add billing-specific data here
        billing_info = {
            'plan': 'Free',
            'next_payment': 'N/A',
            'payment_method': 'None'
        }
        
        return render_template('user_billing.html', user=user_info, billing=billing_info)
    except Exception as e:
        logger.error(f"Error loading billing page: {str(e)}")
        flash("Error loading billing information", "error")
        return redirect(url_for('dashboard.index'))