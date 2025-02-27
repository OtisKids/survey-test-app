# survey_routes.py
from datetime import datetime
import logging
from typing import Dict, List, Any, Union
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

# Import helpers from a central location to avoid circular imports
from helpers.survey_helpers import (
    load_catalog, load_surveys, load_responses, save_responses,
    calculate_survey_score, calculate_wellbeing_performance, update_dashboard_data
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize the survey blueprint
survey_bp = Blueprint('survey', __name__, template_folder='templates')

@survey_bp.route('/')
@login_required
def index():
    """
    Survey index page - redirects to the catalog.
    """
    return redirect(url_for('survey.catalog'))

@survey_bp.route('/take/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id: int):
    """
    Route to take a survey by its survey_id.

    GET: Render the survey for answering.
    POST: Process and save user responses.
    """
    try:
        surveys = load_surveys()
        survey_item = next((s for s in surveys.get("surveys", []) if s.get("id") == survey_id), None)

        if not survey_item:
            flash("Survey not found", "error")
            return redirect(url_for('dashboard_bp.dashboard'))

        if request.method == 'POST':
            answers = []
            # Get answers for each question
            for idx, question in enumerate(survey_item.get("questions", [])):
                answer_key = f"question_{idx}"
                answer = request.form.get(answer_key, "")
                
                # Better handling of numeric conversion
                try:
                    # Handle both integer and decimal inputs
                    answers.append(float(answer) if answer.strip() else 0)
                except ValueError:
                    logger.warning(f"Non-numeric answer provided for question {idx}: {answer}")
                    answers.append(0)
            
            # Save response data
            username = session.get('username')
            if not username:
                flash("You must be logged in to submit surveys", "error")
                return redirect(url_for('user_bp.login'))
                
            # Save response
            responses = load_responses()
            responses.append({
                "username": username,
                "survey_id": survey_id,
                "survey_type": "standard",
                "timestamp": datetime.now().isoformat(),
                "answers": answers
            })
            save_responses(responses)

            # Calculate survey metrics
            try:
                survey_score = calculate_survey_score(answers)
                wellbeing_performance = calculate_wellbeing_performance(answers, survey_item.get("questions", []))
                update_dashboard_data(username, survey_score, wellbeing_performance)
                flash("Thank you for submitting the survey!", "success")
            except Exception as e:
                logger.error(f"Error calculating survey metrics: {str(e)}")
                flash("Your response was saved, but there was an error calculating your results.", "warning")
            
            return redirect(url_for('dashboard_bp.dashboard'))

        return render_template('surveys/take_survey.html', survey=survey_item)
        
    except Exception as e:
        logger.error(f"Error in take_survey: {str(e)}")
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for('dashboard_bp.dashboard'))

# ---------------------------
# Catalog Routes
# ---------------------------

@survey_bp.route('/catalog')
@login_required
def catalog():
    """
    Display the survey catalog.
    """
    try:
        catalog_data = load_catalog()
        surveys = catalog_data.get("surveys", [])
        allowed_categories = catalog_data.get("allowedCategories", [])
        
        # Add completion status for each survey
        responses = load_responses()
        username = session.get('username')
        completed_survey_keys = [
            r.get("survey_key") for r in responses 
            if r.get("username") == username and r.get("survey_key")
        ]
        
        for survey in surveys:
            survey["completed"] = str(survey.get("id", "")) in completed_survey_keys
            
        return render_template(
            'surveys/catalog.html', 
            catalog=surveys, 
            allowedCategories=allowed_categories
        )
        
    except Exception as e:
        logger.error(f"Error in catalog: {str(e)}")
        flash("An error occurred loading the survey catalog.", "error")
        return redirect(url_for('dashboard_bp.dashboard'))

@survey_bp.route('/take_catalog/<string:survey_key>', methods=['GET', 'POST'])
@login_required
def take_catalog_survey(survey_key: str):
    """
    Take a survey from the catalog by its key.
    """
    try:
        catalog_data = load_catalog()
        surveys = catalog_data.get("surveys", [])
        survey_item = next((s for s in surveys if str(s.get("id", "")) == survey_key), None)

        if not survey_item:
            flash("Survey not found in the catalog", "error")
            return redirect(url_for('survey.catalog'))

        if request.method == 'POST':
            # Create a structured response format that matches take_survey
            answers = {}
            for idx, question in enumerate(survey_item.get("questions", [])):
                answer_key = f"question_{idx}"
                answers[answer_key] = request.form.get(answer_key, "")
            
            username = session.get('username')
            if not username:
                flash("You must be logged in to submit surveys", "error")
                return redirect(url_for('user_bp.login'))
                
            # Save response with metadata
            responses = load_responses()
            responses.append({
                "username": username,
                "survey_key": survey_key,
                "survey_type": "catalog",
                "timestamp": datetime.now().isoformat(),
                "answers": answers
            })
            save_responses(responses)
            flash("Thank you for submitting the catalog survey!", "success")
            return redirect(url_for('survey.catalog'))

        return render_template('surveys/take_survey_catalog.html', survey=survey_item, survey_key=survey_key)
        
    except Exception as e:
        logger.error(f"Error in take_catalog_survey: {str(e)}")
        flash("An unexpected error occurred while processing the survey.", "error")
        return redirect(url_for('survey.catalog'))

# Additional routes for survey management, reporting, etc. could be added here