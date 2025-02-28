# helpers/survey_helpers.py
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def load_json_file(filename: str) -> Dict:
    """
    Load data from a JSON file
    
    Args:
        filename (str): Path to the JSON file
        
    Returns:
        dict: Loaded data or empty dict if file not found
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"File not found: {filename}")
            return {}
    except Exception as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        return {}

def save_json_file(filename: str, data: Any) -> bool:
    """
    Save data to a JSON file
    
    Args:
        filename (str): Path to the JSON file
        data (Any): Data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {str(e)}")
        return False

def load_users() -> Dict:
    """Load users from the users.json file"""
    return load_json_file(os.environ.get('USERS_FILE', 'users.json'))

def save_users(users: Dict) -> bool:
    """Save users to the users.json file"""
    return save_json_file(os.environ.get('USERS_FILE', 'users.json'), users)

def load_catalog() -> Dict:
    """Load survey catalog from the catalog file"""
    return load_json_file(os.environ.get('CATALOG_FILE', 'survey_catalog.json'))

def load_surveys() -> Dict:
    """Load surveys from the surveys file"""
    return load_json_file(os.environ.get('SURVEYS_FILE', 'surveys.json'))

def load_responses() -> List:
    """Load survey responses from the responses file"""
    data = load_json_file(os.environ.get('RESPONSES_FILE', 'responses.json'))
    return data if isinstance(data, list) else []

def save_responses(responses: List) -> bool:
    """Save survey responses to the responses file"""
    return save_json_file(os.environ.get('RESPONSES_FILE', 'responses.json'), responses)

def calculate_survey_score(answers: List[float]) -> float:
    """
    Calculate the overall score for a survey based on answers
    
    Args:
        answers (List[float]): List of numeric answers
        
    Returns:
        float: Calculated score
    """
    if not answers:
        return 0
    
    # Simple average for now - you may want to implement your specific scoring algorithm
    return sum(answers) / len(answers)

def calculate_wellbeing_performance(answers: List[float], questions: List[Dict]) -> Dict:
    """
    Calculate wellbeing performance metrics from survey answers
    
    Args:
        answers (List[float]): List of numeric answers
        questions (List[Dict]): List of question objects
        
    Returns:
        Dict: Wellbeing performance metrics
    """
    if not answers or not questions:
        return {}
    
    # Group questions by category
    categories = {}
    for i, question in enumerate(questions):
        if i < len(answers):
            category = question.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(answers[i])
    
    # Calculate average score for each category
    performance = {}
    for category, scores in categories.items():
        if scores:
            performance[category] = sum(scores) / len(scores)
    
    return performance

def update_dashboard_data(username: str, survey_score: float, wellbeing_performance: Dict) -> bool:
    """
    Update user's dashboard data with new survey results
    
    Args:
        username (str): Username
        survey_score (float): Overall survey score
        wellbeing_performance (Dict): Wellbeing metrics by category
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load existing dashboard data if available
        dashboard_file = f"dashboard_{username}.json"
        dashboard_data = load_json_file(dashboard_file)
        
        # Initialize if empty
        if not dashboard_data:
            dashboard_data = {
                'username': username,
                'survey_history': [],
                'wellbeing_trends': {}
            }
        
        # Add new survey data
        timestamp = datetime.now().isoformat()
        dashboard_data['survey_history'].append({
            'timestamp': timestamp,
            'score': survey_score
        })
        
        # Update wellbeing trends
        for category, score in wellbeing_performance.items():
            if category not in dashboard_data['wellbeing_trends']:
                dashboard_data['wellbeing_trends'][category] = []
            
            dashboard_data['wellbeing_trends'][category].append({
                'timestamp': timestamp,
                'score': score
            })
        
        # Save updated data
        return save_json_file(dashboard_file, dashboard_data)
        
    except Exception as e:
        logger.error(f"Error updating dashboard data: {str(e)}")
        return False

def get_user_dashboard_data(username: str) -> Dict:
    """
    Get dashboard data for a specific user
    
    Args:
        username (str): Username
        
    Returns:
        Dict: Dashboard data or empty dict if not found
    """
    dashboard_file = f"dashboard_{username}.json"
    return load_json_file(dashboard_file)