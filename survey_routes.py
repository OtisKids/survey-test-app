import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

survey_bp = Blueprint('survey', __name__)

TEMPLATES_FILE = 'survey_templates.json'
SURVEYS_FILE = 'surveys.json'
RESPONSES_FILE = 'responses.json'
CATALOG_FILE = 'survey_catalog.json'  # New file for the catalog

def load_templates():
    try:
        with open(TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        templates = {"templates": []}
    return templates

def save_templates(templates):
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump(templates, f, indent=2)

def load_surveys():
    try:
        with open(SURVEYS_FILE, 'r') as f:
            surveys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        surveys = {"surveys": []}
    return surveys

def save_surveys(surveys):
    with open(SURVEYS_FILE, 'w') as f:
        json.dump(surveys, f, indent=2)

def load_responses():
    try:
        with open(RESPONSES_FILE, 'r') as f:
            responses = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        responses = []
    return responses

def save_responses(responses):
    with open(RESPONSES_FILE, 'w') as f:
        json.dump(responses, f, indent=2)

# --- New helper functions for Catalog ---
def load_catalog():
    try:
        with open(CATALOG_FILE, 'r') as f:
            catalog = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        catalog = {}
    return catalog

def save_catalog(catalog):
    with open(CATALOG_FILE, 'w') as f:
        json.dump(catalog, f, indent=2)

def login_required(f):
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
    templates = load_templates()
    surveys = load_surveys()
    return render_template('survey_details.html',
                           templates=templates["templates"],
                           surveys=surveys.get("surveys", []))

@survey_bp.route('/customize/<int:template_id>', methods=['GET', 'POST'])
@login_required
def customize_survey(template_id):
    templates = load_templates()
    template = next((t for t in templates["templates"] if t["id"] == template_id), None)
    if not template:
        flash("Template not found", "error")
        return redirect(url_for('survey.dashboard_surveys'))
    if request.method == 'POST':
        template['title'] = request.form.get('title', template['title']).strip()
        questions = request.form.getlist('questions[]')
        if questions:
            template['questions'] = questions
        save_templates(templates)
        flash("Template updated!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('customize_survey.html', template=template)

@survey_bp.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    templates = load_templates()
    template = next((t for t in templates["templates"] if t["id"] == template_id), None)
    if not template:
        flash("Template not found", "error")
        return redirect(url_for('survey.dashboard_surveys'))
    if request.method == 'POST':
        template['title'] = request.form.get('title', template['title']).strip()
        questions = request.form.getlist('questions[]')
        if questions:
            template['questions'] = questions
        save_templates(templates)
        flash("Template edited successfully!", "success")
        return redirect(url_for('survey.dashboard_surveys'))
    return render_template('edit_template.html', template=template)

# ---------------------------
# Survey Upload and Taking
# ---------------------------
@survey_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_surveys():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            try:
                data = json.load(file)
                surveys = load_surveys()
                surveys["surveys"].extend(data.get("surveys", []))
                save_surveys(surveys)
                # Also update the catalog (if surveys are present in the file)
                catalog = load_catalog()
                # Expecting each survey to have at least an id and title; here we merge them.
                for survey in data.get("surveys", []):
                    # Use integer id if available; otherwise, ensure a unique key.
                    catalog_id = survey.get("id")
                    if catalog_id is not None:
                        catalog[str(catalog_id)] = survey
                save_catalog(catalog)
                flash("Surveys uploaded successfully!", "success")
                return redirect(url_for('survey.dashboard_surveys'))
            except Exception as e:
                flash("Failed to upload surveys: " + str(e), "error")
                return redirect(url_for('survey.upload_surveys'))
        else:
            flash("No file provided", "error")
            return redirect(url_for('survey.upload_surveys'))
    return render_template('upload_surveys.html')

@survey_bp.route('/take/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id):
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
# New: Catalog Routes
# ---------------------------
@survey_bp.route('/catalog')
@login_required
def catalog():
    catalog_data = load_catalog()
    catalog_list = []
    # If the JSON has a key "catalog" and a list value, use that;
    # otherwise, assume the whole file is a dict mapping survey_key -> survey info.
    if "catalog" in catalog_data and isinstance(catalog_data["catalog"], list):
        catalog_list = catalog_data["catalog"]
    else:
        for key, survey in catalog_data.items():
            # Add the key as an id if not already present.
            survey["id"] = key
            catalog_list.append(survey)
    return render_template('catalog.html', catalog=catalog_list)

# New route for taking catalog surveys
@survey_bp.route('/take_catalog/<string:survey_key>', methods=['GET', 'POST'])
@login_required
def take_catalog_survey(survey_key):
    catalog_data = load_catalog()
    survey_item = catalog_data.get(survey_key)
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
