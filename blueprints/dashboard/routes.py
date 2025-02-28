# blueprints/dashboard/routes.py
import logging
from flask import render_template, redirect, url_for, session, flash, request
from helpers.survey_helpers import get_user_dashboard_data, load_users
from blueprints.dashboard import dashboard_bp
from functools import wraps
from helpers.radar import create_wellbeing_radar
from helpers.userdata_helpers import (
    get_user_dashboard_data,
    get_all_wellbeing_scores,
    get_user_stats
)

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

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    try:
        username = session.get('username')
        
        # Get user's wellbeing scores
        wellbeing_data = get_all_wellbeing_scores(username)
        
        # Generate the wellbeing radar chart
        wellbeing_radar = create_wellbeing_radar(wellbeing_data)
        
        # Get user stats
        stats = get_user_stats(username)
        
        # Get full dashboard data for other components
        dashboard_data = get_user_dashboard_data(username)

        # Load additional user info if needed
        users = load_users()  # Assuming this function exists
        user_info = users.get(username, {})

        return render_template(
            'dashboard.html',
            user=user_info,
            dashboard_data=dashboard_data,
            stats=stats,
            wellbeing_radar=wellbeing_radar
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash("Error loading dashboard data", "error")
        # Provide a default empty stats to avoid template errors
        return render_template('dashboard.html', user={}, dashboard_data={}, stats={})


'''
@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    try:
        username = session.get('username')
        user_data = get_user_dashboard_data(username)

        # Load additional user info if needed.
        users = load_users()
        user_info = users.get(username, {})

        # Ensure stats is available
        stats = user_data.get('stats', {})  # if not included in user_data, use default {}.

        return render_template(
            'dashboard.html',
            user=user_info,
            dashboard_data=user_data,
            stats=stats
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash("Error loading dashboard data", "error")
        # Provide a default empty stats to avoid template errors.
        return render_template('dashboard.html', user={}, dashboard_data={}, stats={})
'''

