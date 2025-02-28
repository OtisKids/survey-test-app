# blueprints/survey/routes.py
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, request, session, flash
from helpers.survey_helpers import (
    load_catalog, load_surveys, load_responses, save_responses,
    calculate_survey_score, calculate_wellbeing_performance, update_dashboard_data
)
from blueprints.survey import survey_bp
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

'''
ToDo: when a user complete a survey, we need to get and store its results, update userdata, save history, and mark the survey as completed.
Below is a code for updating userdata

def submit_survey():
    """Process survey submission"""
    try:
        username = session.get('username')
        survey_type = request.form.get('survey_type')
        
        # Collect survey data from form
        survey_data = {}
        for key, value in request.form.items():
            if key.startswith('question_'):
                survey_data[key] = value
        
        # Process survey and update wellbeing scores
        success = process_survey_and_update_wellbeing(username, survey_type, survey_data)
        
        if success:
            flash("Survey completed successfully!", "success")
        else:
            flash("There was an error processing your survey.", "error")
        
        return redirect(url_for('dashboard_bp.index'))
    except Exception as e:
        logger.error(f"Error submitting survey: {str(e)}")
        flash("Error submitting survey", "error")
        return redirect(url_for('dashboard_bp.index'))

'''

@survey_bp.route('/take/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id):
    """Route to take a survey by its survey_id"""
    try:
        surveys = load_surveys()
        survey_item = next((s for s in surveys.get("surveys", []) if s.get("id") == survey_id), None)

        if not survey_item:
            flash("Survey not found", "error")
            return redirect(url_for('dashboard.index'))

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
                return redirect(url_for('auth.login'))
                
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
            
            return redirect(url_for('dashboard.index'))

        return render_template('surveys/take_survey.html', survey=survey_item)
        
    except Exception as e:
        logger.error(f"Error in take_survey: {str(e)}")
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for('dashboard.index'))

@survey_bp.route('/catalog')
@login_required
def catalog():
    """Display the survey catalog"""
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
        return redirect(url_for('dashboard.index'))


        
    except Exception as e:
        logger.error(f"Error in take_catalog_survey: {str(e)}")
        flash("An unexpected error occurred while processing the survey.", "error")
        return redirect(url_for('survey.catalog'))

@survey_bp.route('/details/<int:survey_id>')
@login_required
def survey_details(survey_id):
    """Show details for a specific survey"""
    try:
        # Try loading from both survey sources
        surveys = load_surveys()
        catalog_data = load_catalog()
        
        survey_item = next((s for s in surveys.get("surveys", []) if s.get("id") == survey_id), None)
        
        if not survey_item:
            # Try finding in catalog
            survey_item = next((s for s in catalog_data.get("surveys", []) 
                               if s.get("id") == survey_id), None)
        
        if not survey_item:
            flash("Survey not found", "error")
            return redirect(url_for('survey.catalog'))
            
        return render_template('/surveys/survey_details.html', survey=survey_item)
        
    except Exception as e:
        logger.error(f"Error loading survey details: {str(e)}")
        flash("Error loading survey details", "error")
        return redirect(url_for('survey.catalog'))