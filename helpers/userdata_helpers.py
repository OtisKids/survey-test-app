# helpers.py

import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Constants for wellbeing dimensions
WELLBEING_DIMENSIONS = {
    "Subjective Well-Being": 0,
    "Positive Affect": 0,
    "Life Satisfaction": 0,
    "Material Living Conditions": 0,
    "Quality of Life": 0,
    "Self-acceptance": 0,
    "Positive Relations": 0,
    "Autonomy": 0,
    "Environmental Mastery": 0,
    "Purpose in Life": 0,
    "Personal Growth": 0,
    "Positive Emotion": 0,
    "Engagement": 0,
    "Relationships": 0,
    "Meaning": 0,
    "Accomplishment": 0,
    "Competence": 0,
    "Social Connections": 0,
    "Personal Security": 0
}

# Paths for data storage
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')
USER_DATA_PATH = os.path.join(DATA_DIR, 'user_data.json')

def ensure_data_dir_exists():
    """Make sure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_all_user_data():
    """Load all user data from the JSON file."""
    ensure_data_dir_exists()
    try:
        if os.path.exists(USER_DATA_PATH):
            with open(USER_DATA_PATH, 'r') as file:
                return json.load(file)
        return {}
    except Exception as e:
        logger.error(f"Error loading user data: {str(e)}")
        return {}

def save_all_user_data(all_user_data):
    """Save all user data to the JSON file."""
    ensure_data_dir_exists()
    try:
        with open(USER_DATA_PATH, 'w') as file:
            json.dump(all_user_data, file, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        return False

def get_user_dashboard_data(username):
    """
    Get dashboard data for a specific user.
    
    Args:
        username (str): The username to get data for
        
    Returns:
        dict: User's dashboard data including wellbeing scores
    """
    all_user_data = load_all_user_data()
    
    # If user doesn't exist in data, create default structure
    if username not in all_user_data:
        all_user_data[username] = {
            "wellbeing": WELLBEING_DIMENSIONS.copy(),
            "surveys": [],
            "stats": {
                "surveys_completed": 0,
                "last_survey_date": None,
                "trend": "neutral"
            }
        }
        save_all_user_data(all_user_data)
    
    return all_user_data[username]

def get_wellbeing_score(username, dimension):
    """
    Get a specific wellbeing dimension score for a user.
    
    Args:
        username (str): The username
        dimension (str): The wellbeing dimension
        
    Returns:
        int: The score value (0-10)
    """
    user_data = get_user_dashboard_data(username)
    wellbeing_data = user_data.get('wellbeing', {})
    
    # Return the value if it exists, otherwise return 0
    return wellbeing_data.get(dimension, 0)

def get_all_wellbeing_scores(username):
    """
    Get all wellbeing dimension scores for a user.
    
    Args:
        username (str): The username
        
    Returns:
        dict: Dictionary of dimension:score pairs
    """
    user_data = get_user_dashboard_data(username)
    return user_data.get('wellbeing', WELLBEING_DIMENSIONS.copy())

def set_wellbeing_score(username, dimension, score):
    """
    Set a specific wellbeing dimension score for a user.
    
    Args:
        username (str): The username
        dimension (str): The wellbeing dimension
        score (int): The score value (0-10)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate score
    try:
        score_val = int(score)
        if score_val < 0 or score_val > 10:
            logger.error(f"Invalid score value: {score}. Must be 0-10.")
            return False
    except (ValueError, TypeError):
        logger.error(f"Invalid score value: {score}. Must be an integer.")
        return False
    
    # Validate dimension
    if dimension not in WELLBEING_DIMENSIONS:
        logger.error(f"Invalid dimension: {dimension}")
        return False
    
    all_user_data = load_all_user_data()
    
    # Ensure user exists
    if username not in all_user_data:
        all_user_data[username] = {"wellbeing": WELLBEING_DIMENSIONS.copy(), "surveys": [], "stats": {}}
    
    # Ensure wellbeing section exists
    if "wellbeing" not in all_user_data[username]:
        all_user_data[username]["wellbeing"] = WELLBEING_DIMENSIONS.copy()
    
    # Set the score
    all_user_data[username]["wellbeing"][dimension] = score_val
    
    # Save to file
    return save_all_user_data(all_user_data)

def update_all_wellbeing_scores(username, scores_dict):
    """
    Update multiple wellbeing dimension scores at once.
    
    Args:
        username (str): The username
        scores_dict (dict): Dictionary of dimension:score pairs to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    all_user_data = load_all_user_data()
    
    # Ensure user exists
    if username not in all_user_data:
        all_user_data[username] = {"wellbeing": WELLBEING_DIMENSIONS.copy(), "surveys": [], "stats": {}}
    
    # Ensure wellbeing section exists
    if "wellbeing" not in all_user_data[username]:
        all_user_data[username]["wellbeing"] = WELLBEING_DIMENSIONS.copy()
    
    # Validate and update each score
    for dimension, score in scores_dict.items():
        if dimension not in WELLBEING_DIMENSIONS:
            logger.warning(f"Skipping invalid dimension: {dimension}")
            continue
        
        try:
            score_val = int(score)
            if 0 <= score_val <= 10:
                all_user_data[username]["wellbeing"][dimension] = score_val
            else:
                logger.warning(f"Skipping invalid score for {dimension}: {score}. Must be 0-10.")
        except (ValueError, TypeError):
            logger.warning(f"Skipping invalid score for {dimension}: {score}. Must be an integer.")
    
    # Save to file
    return save_all_user_data(all_user_data)

def record_survey_completion(username, survey_type, survey_data=None):
    """
    Record that a user completed a survey and update stats.
    
    Args:
        username (str): The username
        survey_type (str): The type of survey completed
        survey_data (dict, optional): Survey response data
        
    Returns:
        bool: True if successful, False otherwise
    """
    all_user_data = load_all_user_data()
    
    # Ensure user exists
    if username not in all_user_data:
        all_user_data[username] = {"wellbeing": WELLBEING_DIMENSIONS.copy(), "surveys": [], "stats": {}}
    
    # Ensure surveys and stats sections exist
    if "surveys" not in all_user_data[username]:
        all_user_data[username]["surveys"] = []
    
    if "stats" not in all_user_data[username]:
        all_user_data[username]["stats"] = {"surveys_completed": 0, "last_survey_date": None, "trend": "neutral"}
    
    # Get current datetime
    now = datetime.now().isoformat()
    
    # Create survey record
    survey_record = {
        "survey_type": survey_type,
        "completed_at": now,
        "data": survey_data if survey_data else {}
    }
    
    # Add to surveys list
    all_user_data[username]["surveys"].append(survey_record)
    
    # Update stats
    all_user_data[username]["stats"]["surveys_completed"] = len(all_user_data[username]["surveys"])
    all_user_data[username]["stats"]["last_survey_date"] = now
    
    # Determine trend (simple implementation, can be enhanced)
    if len(all_user_data[username]["surveys"]) > 1:
        # For a simple trend, just use improving for now
        all_user_data[username]["stats"]["trend"] = "improving"
    
    # Save to file
    return save_all_user_data(all_user_data)

def calculate_wellbeing_from_survey(survey_data):
    """
    Calculate wellbeing scores from survey data.
    
    Args:
        survey_data (dict): Survey response data
        
    Returns:
        dict: Calculated wellbeing scores
    """
    wellbeing_scores = WELLBEING_DIMENSIONS.copy()
    
    # This is a placeholder implementation
    # You'll need to implement your specific survey interpretation logic here
    # For example, mapping specific survey questions to wellbeing dimensions
    
    # Example (replace with your actual logic):
    if "question1" in survey_data:
        wellbeing_scores["Positive Affect"] = int(survey_data["question1"]) 
    
    if "question2" in survey_data:
        wellbeing_scores["Life Satisfaction"] = int(survey_data["question2"])
    
    # ... and so on for other dimensions
    
    return wellbeing_scores

def process_survey_and_update_wellbeing(username, survey_type, survey_data):
    """
    Process survey results and update user's wellbeing scores.
    
    Args:
        username (str): The username
        survey_type (str): The type of survey completed
        survey_data (dict): Survey response data
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Calculate wellbeing scores from the survey
    wellbeing_scores = calculate_wellbeing_from_survey(survey_data)
    
    # Update user's wellbeing scores
    success = update_all_wellbeing_scores(username, wellbeing_scores)
    
    # Record the survey completion
    if success:
        record_survey_completion(username, survey_type, survey_data)
    
    return success

def get_user_survey_history(username):
    """
    Get a user's survey completion history.
    
    Args:
        username (str): The username
        
    Returns:
        list: List of survey completion records
    """
    user_data = get_user_dashboard_data(username)
    return user_data.get('surveys', [])

def get_user_stats(username):
    """
    Get user statistics.
    
    Args:
        username (str): The username
        
    Returns:
        dict: User statistics
    """
    user_data = get_user_dashboard_data(username)
    return user_data.get('stats', {"surveys_completed": 0, "last_survey_date": None, "trend": "neutral"})

def reset_wellbeing_data(username):
    """
    Reset a user's wellbeing data to default values.
    
    Args:
        username (str): The username
        
    Returns:
        bool: True if successful, False otherwise
    """
    all_user_data = load_all_user_data()
    
    if username in all_user_data:
        all_user_data[username]["wellbeing"] = WELLBEING_DIMENSIONS.copy()
        return save_all_user_data(all_user_data)
    
    return False

def delete_user_data(username):
    """
    Delete all data for a user.
    
    Args:
        username (str): The username
        
    Returns:
        bool: True if successful, False otherwise
    """
    all_user_data = load_all_user_data()
    
    if username in all_user_data:
        del all_user_data[username]
        return save_all_user_data(all_user_data)
    
    return False
