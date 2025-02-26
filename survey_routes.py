import json
import logging
from typing import Any, Dict, List, Union
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

# Configure logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

survey_bp = Blueprint('survey', __name__)

# File paths
TEMPLATES_FILE = 'survey_templates.json'
SURVEYS_FILE = 'surveys.json'
RESPONSES_FILE = 'responses.json'
CATALOG_FILE = 'survey_catalog.json'  # File for the catalog

# ---------------------------
# Helper Functions
# ---------------------------
def load_json_file(filename: str, default: Union[dict, list]) -> Union[dict, list]:
    """Load JSON data from a file, returning a default value on error."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load {filename}: {e}")
        return default

def save_json_file(filename: str, data: Any) -> None:
    """Save JSON data to a file."""
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
    """Decorator to ensure a user is logged in before accessing protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------
# Survey Template Routes
# ---------------------------

@survey_bp.route('/create_template', methods=['GET', 'POST'])
@login_required
def create_template():
    """
    Create a new survey template.
    
    GET: Render the creation form.
    POST: Process the form and save the new template.
    """
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        questions = request.form.getlist('questions[]')
        templates = load_templates()
        new_template = {
            "id": len(templates["templates"]) + 1,
            "title": title,
            "questions": questions
        }
        templates["templates"].append(new_template)
        save_templates(templates)
        flash("Survey template created!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('create_template.html')

@survey_bp.route('/dashboard_surveys')
@login_required
def dashboard_surveys():
    """
    Dashboard view for surveys that shows both templates and surveys.
    """
    templates = load_templates()
    surveys = load_surveys()
    return render_template('survey_details.html',
                           templates=templates.get("templates", []),
                           surveys=surveys.get("surveys", []))

@survey_bp.route('/customize/<int:template_id>', methods=['GET', 'POST'])
@login_required
def customize_survey(template_id: int):
    """
    Customize an existing survey template.
    
    GET: Render a customization form.
    POST: Update template title and questions.
    """
    templates = load_templates()
    template = next((t for t in templates.get("templates", []) if t.get("id") == template_id), None)
    if not template:
        flash("Template not found", "error")
        return redirect(url_for('survey.dashboard_surveys'))
    if request.method == 'POST':
        template['title'] = request.form.get('title', template.get('title', '')).strip()
        questions = request.form.getlist('questions[]')
        if questions:
            template['questions'] = questions
        save_templates(templates)
        flash("Template updated!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('customize_survey.html', template=template)

@survey_bp.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id: int):
    """
    Edit a survey template.
    
    GET: Render the edit form.
    POST: Save the edited template details.
    """
    templates = load_templates()
    template = next((t for t in templates.get("templates", []) if t.get("id") == template_id), None)
    if not template:
        flash("Template not found", "error")
        return redirect(url_for('survey.dashboard_surveys'))
    if request.method == 'POST':
        template['title'] = request.form.get('title', template.get('title', '')).strip()
        questions = request.form.getlist('questions[]')
        if questions:
            template['questions'] = questions
        save_templates(templates)
        flash("Template edited successfully!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('edit_template.html', template=template)

# ---------------------------
# Survey Upload and Taking Routes
# ---------------------------

@survey_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_surveys():
    """
    Upload surveys from a JSON file.
    
    GET: Render the upload form.
    POST: Process and save uploaded survey data.
    """
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            try:
                data = json.load(file)
                surveys = load_surveys()
                surveys["surveys"].extend(data.get("surveys", []))
                save_surveys(surveys)
                # Update the catalog if surveys are provided in the file.
                # Assumes the file doesn't include the "allowedCategories" key.
                catalog = load_catalog()
                # Initialize catalog structure if necessary:
                if not catalog.get("surveys"):
                    catalog["surveys"] = []
                for survey in data.get("surveys", []):
                    # Ensure survey id exists.
                    if "id" in survey:
                        catalog["surveys"].append(survey)
                save_catalog(catalog)
                flash("Surveys uploaded successfully!", "success")
                return redirect(url_for('survey.dashboard_surveys'))
            except Exception as e:
                logger.error(f"Error processing uploaded file: {e}")
                flash("Failed to upload surveys: " + str(e), "error")
                return redirect(url_for('survey.upload_surveys'))
        else:
            flash("No file provided", "error")
            return redirect(url_for('survey.upload_surveys'))
    return render_template('upload_surveys.html')

@survey_bp.route('/take/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id: int):
    """
    Route to take a survey by its survey_id.
    
    GET: Render the survey for answering.
    POST: Process user responses.
    """
    surveys = load_surveys()
    survey_item = next((s for s in surveys.get("surveys", []) if s.get("id") == survey_id), None)
    if not survey_item:
        flash("Survey not found", "error")
        return redirect(url_for('survey.dashboard_surveys'))
    if request.method == 'POST':
        answers = {}
        for idx, question in enumerate(survey_item.get("questions", [])):
            answers[f"question_{idx}"] = request.form.get(f"question_{idx}", "")
        responses = load_responses()
        responses.append({
            "username": session['username'],
            "survey_id": survey_id,
            "answers": answers
        })
        save_responses(responses)
        flash("Thank you for submitting the survey!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('take_survey.html', survey=survey_item)

# ---------------------------
# Catalog Routes
# ---------------------------

@survey_bp.route('/catalog')
@login_required
def catalog():
    """
    Display the survey catalog.
    
    The catalog JSON is expected to have the keys:
      - "allowedCategories": list of category names
      - "surveys": list of survey objects
    """
    catalog_data = load_catalog()
    surveys = catalog_data.get("surveys", [])
    allowedCategories = catalog_data.get("allowedCategories", [])
    return render_template('catalog.html', catalog=surveys, allowedCategories=allowedCategories)

@survey_bp.route('/take_catalog/<string:survey_key>', methods=['GET', 'POST'])
@login_required
def take_catalog_survey(survey_key: str):
    """
    Take a survey from the catalog by its key.
    
    GET: Render the catalog survey.
    POST: Process the submission of catalog survey responses.
    """
    catalog_data = load_catalog()
    # Look for the survey in the catalog "surveys" list by matching the survey id (always converted to string)
    surveys = catalog_data.get("surveys", [])
    survey_item = next((s for s in surveys if str(s.get("id", "")) == survey_key), None)
    if not survey_item:
        flash("Survey not found in the catalog", "error")
        return redirect(url_for('survey.catalog'))
    if request.method == 'POST':
        answers = {}
        for idx, question in enumerate(survey_item.get("questions", [])):
            answers[f"question_{idx}"] = request.form.get(f"question_{idx}", "")
        responses = load_responses()
        responses.append({
            "username": session['username'],
            "survey_key": survey_key,
            "answers": answers
        })
        save_responses(responses)
        flash("Thank you for submitting the catalog survey!", "success")
        return redirect(url_for('survey.catalog'))
    return render_template('take_survey_catalog.html', survey=survey_item, survey_key=survey_key)
