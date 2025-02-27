from flask import Blueprint, flash, redirect, render_template, session, url_for
from app import load_catalog, survey_helpers
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('user.login'))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/')
@login_required
def dashboard():
    """
    Main dashboard route.
    Displays an overview of the user's activity, surveys, and stats.
    """
    dashboard_data = survey_helpers.load_dashboard_data()
    user_data = dashboard_data.get(session['username'], {})

    # Calculate average survey score
    survey_scores = user_data.get('survey_scores', [])
    avg_survey_score = sum(survey_scores) / len(survey_scores) if survey_scores else 0

    # Calculate latest wellbeing performance
    wellbeing_performances = user_data.get('wellbeing_performance', [])
    latest_wellbeing_performance = wellbeing_performances[-1] if wellbeing_performances else {}

    # Create radar graph
    radar_graph_html = survey_helpers.create_radar_graph(latest_wellbeing_performance)

    # Calculate stats for the dashboard
    stats = survey_helpers.calculate_stats(user_data)

    # Fetch recent activities
    recent_activities = survey_helpers.fetch_recent_activities(user_data)

    return render_template('dashboard.html',
                           avg_survey_score=avg_survey_score,
                           latest_wellbeing_performance=latest_wellbeing_performance,
                           radar_graph_html=radar_graph_html,
                           stats=stats,
                           recent_activities=recent_activities)




@dashboard_bp.route('/history')
@login_required
def history():
    responses = survey_helpers.load_responses()
    user_responses = [r for r in responses if r.get('username') == session['username']]
    surveys = survey_helpers.load_surveys()
    survey_dict = {s.get('id'): s for s in surveys.get('surveys', [])}
    # Calculate survey scores and wellbeing performance for each response
    for response in user_responses:
        survey = survey_dict.get(response['survey_id'])
        if survey:
            response['survey_score'] = survey_helpers.calculate_survey_score(response['answers'])
            response['wellbeing_performance'] = survey_helpers.calculate_wellbeing_performance(response['answers'], survey.get('questions', []))
    return render_template('dashboard_history.html', responses=user_responses, survey_dict=survey_dict)

@dashboard_bp.route('/profile')
@login_required
def profile():
    user_info = {
        'username': session.get('username', 'Unknown User'),
        'email': session.get('email', '')
    }
    return render_template('dashboard_profile.html', user=user_info)
