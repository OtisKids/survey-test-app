import uuid
import json
import logging
from typing import Any, Dict, List, Tuple, Union
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import plotly.graph_objects as go
from datetime import datetime, timedelta
from flask_login import login_required
import app

# Configure logging for this module. In a production system consider centralizing logging config.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths (Consider moving these to a centralized configuration in the future)
TEMPLATES_FILE = 'survey_templates.json'
SURVEYS_FILE = 'surveys.json'
RESPONSES_FILE = 'responses.json'
CATALOG_FILE = 'survey_catalog.json'
DASHBOARD_FILE = 'dashboard_data.json'

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.

    Args:
        file_path: The path to the JSON file.

    Returns:
        A dictionary parsed from the JSON file or an empty dictionary in case of errors.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Unable to load file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a JSON file.

    Args:
        file_path: The path to the JSON file.
        data: The dictionary containing data.
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")

def load_users() -> Dict[str, Any]:
    """
    Load users from the JSON file defined in configuration.

    Returns:
        A dictionary of users or an empty dictionary in case of errors.
    """
    return load_json_file(app.config['USERS_FILE'])

def save_users(users: Dict[str, Any]) -> None:
    """
    Save the users dictionary to the JSON file defined in configuration.

    Args:
        users: The dictionary containing user data.
    """
    save_json_file(app.config['USERS_FILE'], users)

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

    Handles legacy and new formats.

    Returns:
        A list of survey dictionaries.
    """
    catalog_data = load_json_file(app.config['CATALOG_FILE'])

    # If legacy format (a list), convert to new format.
    if isinstance(catalog_data, list):
        catalog_data = {"allowedCategories": [], "surveys": catalog_data}

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

def compute_average_rating(survey: Dict[str, Any]) -> float:
    """
    Compute the average rating for a survey.
    If there are no ratings, default to 4.

    Args:
        survey: The survey dictionary containing ratings.

    Returns:
        The average rating.
    """
    ratings = survey.get("ratings", [])
    return round(sum(ratings) / len(ratings), 2) if ratings else 4

def generate_unique_id() -> str:
    """
    Generate a unique identifier for a survey instance.

    Returns:
        A unique identifier string.
    """
    return str(uuid.uuid4())

def load_json_file(filename: str, default: Union[dict, list]) -> Union[dict, list]:
    """
    Load JSON data from a file.

    Args:
        filename: The path to the JSON file.
        default: The default value to return if loading fails.

    Returns:
        The loaded JSON data or the default value if an error occurs.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load {filename}: {e}")
        return default

def save_json_file(filename: str, data: Any) -> None:
    """
    Save JSON data to a file.

    Args:
        filename: The path to the file.
        data: The data to save.
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")

def load_templates() -> Dict[str, List[Dict[str, Any]]]:
    """Load survey templates."""
    return load_json_file(TEMPLATES_FILE, {"templates": []})

def save_templates(templates: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save survey templates."""
    save_json_file(TEMPLATES_FILE, templates)

def load_surveys() -> Dict[str, List[Dict[str, Any]]]:
    """Load surveys."""
    return load_json_file(SURVEYS_FILE, {"surveys": []})

def save_surveys(surveys: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save surveys."""
    save_json_file(SURVEYS_FILE, surveys)

def load_responses() -> List[Dict[str, Any]]:
    """Load survey responses."""
    return load_json_file(RESPONSES_FILE, [])

def save_responses(responses: List[Dict[str, Any]]) -> None:
    """Save survey responses."""
    save_json_file(RESPONSES_FILE, responses)

def load_catalog() -> Dict[str, Any]:
    """Load the survey catalog."""
    return load_json_file(CATALOG_FILE, {})

def save_catalog(catalog: Dict[str, Any]) -> None:
    """Save the survey catalog."""
    save_json_file(CATALOG_FILE, catalog)

def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing protected routes.
    If the user is not logged in, they are redirected to the login page with an error message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def update_dashboard_data(username: str, survey_score: float, wellbeing_performance: Dict[str, float]) -> None:
    """
    Update the dashboard data for a user with new survey results.

    Args:
        username: The username of the user.
        survey_score: The survey score to add.
        wellbeing_performance: The wellbeing performance data to add.
    """
    dashboard_data = load_dashboard_data()
    if username not in dashboard_data:
        dashboard_data[username] = {
            'survey_scores': [],
            'wellbeing_performance': []
        }

    dashboard_data[username]['survey_scores'].append(survey_score)
    dashboard_data[username]['wellbeing_performance'].append(wellbeing_performance)
    save_dashboard_data(dashboard_data)

def load_dashboard_data() -> Dict[str, Any]:
    """Load the dashboard data."""
    return load_json_file(DASHBOARD_FILE, {})

def save_dashboard_data(data: Dict[str, Any]) -> None:
    """Save the dashboard data."""
    save_json_file(DASHBOARD_FILE, data)

def create_radar_graph(wellbeing_data: Dict[str, float]) -> str:
    """
    Create a radar graph for wellbeing performance data.

    Args:
        wellbeing_data: A dictionary containing wellbeing performance data.

    Returns:
        The HTML representation of the radar graph.
    """
    categories = ['Life Satisfaction', 'Emotional Balance', 'Happiness', 'Engagement', 'Social Relationships', 'Purpose & Meaning', 'Accomplishment', 'Self-Rated Health', 'Mental Health']

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=[wellbeing_data.get('life_satisfaction', 5), wellbeing_data.get('emotional_balance', 5), wellbeing_data.get('happiness', 5),
           wellbeing_data.get('engagement', 5), wellbeing_data.get('social_relationships', 5), wellbeing_data.get('purpose_meaning', 5),
           wellbeing_data.get('accomplishment', 5), wellbeing_data.get('self_rated_health', 5), wellbeing_data.get('mental_health', 5)],
        theta=categories,
        fill='toself',
        name='Wellbeing'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False
    )

    return fig.to_html(full_html=False)

def calculate_wellbeing_performance(responses: List[float], survey_questions: List[str]) -> Dict[str, float]:
    """
    Calculate wellbeing performance based on survey responses.

    Args:
        responses: A list of survey responses.
        survey_questions: A list of survey questions.

    Returns:
        A dictionary containing wellbeing performance data.
    """
    categories = {
        'life_satisfaction': [],
        'emotional_balance': [],
        'happiness': [],
        'engagement': [],
        'social_relationships': [],
        'purpose_meaning': [],
        'accomplishment': [],
        'self_rated_health': [],
        'mental_health': []
    }

    for question, response in zip(survey_questions, responses):
        if 'life_satisfaction' in question:
            categories['life_satisfaction'].append(response)
        elif 'emotional_balance' in question:
            categories['emotional_balance'].append(response)
        elif 'happiness' in question:
            categories['happiness'].append(response)
        elif 'engagement' in question:
            categories['engagement'].append(response)
        elif 'social_relationships' in question:
            categories['social_relationships'].append(response)
        elif 'purpose_meaning' in question:
            categories['purpose_meaning'].append(response)
        elif 'accomplishment' in question:
            categories['accomplishment'].append(response)
        elif 'self_rated_health' in question:
            categories['self_rated_health'].append(response)
        elif 'mental_health' in question:
            categories['mental_health'].append(response)

    performance = {}
    for category, values in categories.items():
        performance[category] = sum(values) / len(values) if values else 0

    return performance

def calculate_survey_score(responses: List[float]) -> float:
    """
    Calculate the average survey score.

    Args:
        responses: A list of numeric survey responses.

    Returns:
        The average survey score.
    """
    return sum(responses) / len(responses) if responses else 0

def calculate_stats(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate various statistics based on user data.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A dictionary containing calculated statistics.
    """
    surveys_completed = len(user_data.get('survey_scores', []))
    surveys_completed_trend = get_surveys_completed_trend(user_data)

    consecutive_days = get_consecutive_days(user_data)
    consecutive_days_trend = get_consecutive_days_trend(user_data)

    average_mood = get_average_mood(user_data)
    average_mood_trend, average_mood_trend_class = get_average_mood_trend(user_data)

    mindfulness_score = get_mindfulness_score(user_data)
    mindfulness_score_trend, mindfulness_score_trend_class = get_mindfulness_score_trend(user_data)

    return {
        'surveys_completed': surveys_completed,
        'surveys_completed_trend': surveys_completed_trend,
        'consecutive_days': consecutive_days,
        'consecutive_days_trend': consecutive_days_trend,
        'average_mood': average_mood,
        'average_mood_trend': average_mood_trend,
        'average_mood_trend_class': average_mood_trend_class,
        'mindfulness_score': mindfulness_score,
        'mindfulness_score_trend': mindfulness_score_trend,
        'mindfulness_score_trend_class': mindfulness_score_trend_class
    }

def fetch_recent_activities(user_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fetch the recent activities of the user.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A list of recent activities.
    """
    recent_activities = []

    # Example: Assuming user_data has a list of 'activities' with dictionaries containing 'title', 'message', and 'date'
    activities = user_data.get('activities', [])
    for activity in activities[-3:]:  # Get the last three activities
        recent_activities.append({
            'title': activity.get('title', 'Unknown'),
            'message': activity.get('message', 'No details'),
            'date': activity.get('date', 'Unknown Date')
        })

    return recent_activities

def get_surveys_completed_trend(user_data: Dict[str, Any]) -> str:
    """
    Calculate the trend in surveys completed over the last week.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A string describing the trend.
    """
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)

    recent_surveys = sum(1 for date in user_data.get('survey_dates', []) if datetime.strptime(date, '%Y-%m-%d').date() >= one_week_ago)
    last_week_surveys = sum(1 for date in user_data.get('survey_dates', []) if one_week_ago <= datetime.strptime(date, '%Y-%m-%d').date() < today - timedelta(days=7))

    trend = recent_surveys - last_week_surveys
    if trend > 0:
        return f'+{trend} from last week'
    elif trend < 0:
        return f'{trend} from last week'
    else:
        return 'No change from last week'

def get_consecutive_days(user_data: Dict[str, Any]) -> int:
    """
    Calculate the number of consecutive days with completed surveys.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        The number of consecutive days.
    """
    if not user_data.get('survey_dates'):
        return 0

    today = datetime.now().date()
    survey_dates = sorted([datetime.strptime(date, '%Y-%m-%d').date() for date in user_data['survey_dates']], reverse=True)

    consecutive_days = 0
    for date in survey_dates:
        if date == today - timedelta(days=consecutive_days):
            consecutive_days += 1
        else:
            break

    return consecutive_days

def get_consecutive_days_trend(user_data: Dict[str, Any]) -> str:
    """
    Provide a trend message for consecutive days.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A string describing the trend.
    """
    consecutive_days = get_consecutive_days(user_data)
    if consecutive_days >= 7:
        return 'Keep it up!'
    elif consecutive_days >= 3:
        return 'Good progress!'
    else:
        return 'Start a streak!'

def get_average_mood(user_data: Dict[str, Any]) -> str:
    """
    Calculate the average mood of the user.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A string describing the average mood.
    """
    mood_scores = user_data.get('mood_scores', [])
    if not mood_scores:
        return 'Unknown'

    avg_mood = sum(mood_scores) / len(mood_scores)
    if avg_mood >= 4:
        return 'Good'
    elif avg_mood >= 3:
        return 'Neutral'
    else:
        return 'Poor'

def get_average_mood_trend(user_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Calculate the trend in average mood over the last week.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A tuple containing the trend description and trend class.
    """
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)

    recent_mood_scores = [score for date, score in zip(user_data.get('survey_dates', []), user_data.get('mood_scores', [])) if datetime.strptime(date, '%Y-%m-%d').date() >= one_week_ago]
    last_week_mood_scores = [score for date, score in zip(user_data.get('survey_dates', []), user_data.get('mood_scores', [])) if one_week_ago <= datetime.strptime(date, '%Y-%m-%d').date() < today - timedelta(days=7)]

    if not recent_mood_scores or not last_week_mood_scores:
        return 'Unknown', 'neutral'

    avg_recent_mood = sum(recent_mood_scores) / len(recent_mood_scores)
    avg_last_week_mood = sum(last_week_mood_scores) / len(last_week_mood_scores)

    trend = avg_recent_mood - avg_last_week_mood
    if trend > 0.5:
        return 'Improving', 'positive'
    elif trend < -0.5:
        return 'Declining', 'negative'
    else:
        return 'Stable', 'neutral'

def get_mindfulness_score(user_data: Dict[str, Any]) -> str:
    """
    Calculate the average mindfulness score of the user.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A string describing the average mindfulness score.
    """
    mindfulness_scores = user_data.get('mindfulness_scores', [])
    if not mindfulness_scores:
        return '0/100'

    avg_score = sum(mindfulness_scores) / len(mindfulness_scores)
    return f'{int(avg_score)}/100'

def get_mindfulness_score_trend(user_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Calculate the trend in mindfulness score over the last week.

    Args:
        user_data: A dictionary containing user data.

    Returns:
        A tuple containing the trend description and trend class.
    """
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)

    recent_scores = [score for date, score in zip(user_data.get('survey_dates', []), user_data.get('mindfulness_scores', [])) if datetime.strptime(date, '%Y-%m-%d').date() >= one_week_ago]
    last_week_scores = [score for date, score in zip(user_data.get('survey_dates', []), user_data.get('mindfulness_scores', [])) if one_week_ago <= datetime.strptime(date, '%Y-%m-%d').date() < today - timedelta(days=7)]

    if not recent_scores or not last_week_scores:
        return 'Unknown', 'neutral'

    avg_recent_score = sum(recent_scores) / len(recent_scores)
    avg_last_week_score = sum(last_week_scores) / len(last_week_scores)

    trend = avg_recent_score - avg_last_week_score
    if trend > 5:
        return f'+{int(trend)} points', 'positive'
    elif trend > 0:
        return f'+{int(trend)} points', 'neutral'
    elif trend < -5:
        return f'{int(trend)} points', 'negative'
    elif trend < 0:
        return f'{int(trend)} points', 'neutral'
    else:
        return 'No change', 'neutral'
