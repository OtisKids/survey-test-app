import os
import uuid
import json
from functools import wraps
from flask import Flask, request, redirect, url_for, render_template_string, flash, send_from_directory, session

app = Flask(__name__)
app.secret_key = "secret_for_demo"  # For sessions and flash messages

# -------------------------------
# User Authentication Helpers
# -------------------------------
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        admin_user = {"admin": {"password": "admin"}}
        with open(USERS_FILE, "w") as f:
            json.dump(admin_user, f, indent=4)
        return admin_user
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

users_db = load_users()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# Survey Catalog and Reports Setup
# -------------------------------
REPORTS_DIR = "reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

SURVEY_CATALOG_FILE = "survey_catalog.json"
def load_survey_catalog():
    try:
        with open(SURVEY_CATALOG_FILE, "r") as f:
            catalog = json.load(f)
        return catalog
    except Exception as e:
        print(f"Error loading survey catalog: {e}")
        return {}

SURVEY_CATALOG = load_survey_catalog()

custom_surveys = {}  # Customized surveys storage

# -------------------------------
# Helper Functions for Surveys
# -------------------------------
def generate_unique_id():
    return str(uuid.uuid4())

def calculate_scores(survey_type, responses):
    survey = SURVEY_CATALOG.get(survey_type)
    if not survey:
        return {}
    total, count = 0, 0
    for q in survey.get("questions", []):
        if q.get("type") == "likert":
            try:
                value = int(responses.get(q["id"], 0))
            except ValueError:
                value = 0
            if "negative" in q["id"] or ("reverse" in q.get("note", "").lower()):
                value = 6 - value
            total += value
            count += 1
    overall_score = total / count if count else 0
    return {"overall": overall_score}

def save_report_to_file(instance_id, report_data):
    filename = os.path.join(REPORTS_DIR, f"{instance_id}.json")
    with open(filename, "w") as f:
        json.dump(report_data, f, indent=4)
    return filename

def save_catalog_to_file():
    try:
        with open(SURVEY_CATALOG_FILE, "w") as f:
            json.dump(SURVEY_CATALOG, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving catalog: {e}")
        return False

# -------------------------------
# Routes for Authentication
# -------------------------------
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users_db.get(username)
        if user and user.get("password") == password:
            session["username"] = username
            flash("Logged in successfully.")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("login"))
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Login</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <h1>Login</h1>
      <form method="post">
        <label>Username: <input type="text" name="username" required></label><br>
        <label>Password: <input type="password" name="password" required></label><br>
        <button type="submit">Login</button>
      </form>
      <p>Don't have an account? <a href="{{ url_for('register') }}">Register here</a>.</p>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/logout')
def logout():
    session.pop("username", None)
    flash("Logged out successfully.")
    return redirect(url_for("login"))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users_db:
            flash("Username already exists.")
            return redirect(url_for("register"))
        users_db[username] = {"password": password}
        if save_users(users_db):
            flash("Account created successfully. You can log in now.")
        else:
            flash("Account created but error saving the user database.")
        return redirect(url_for("login"))
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Register</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <h1>Register</h1>
      <form method="post">
        <label>Username: <input type="text" name="username" required></label><br>
        <label>Password: <input type="password" name="password" required></label><br>
        <button type="submit">Register</button>
      </form>
      <p>Already have an account? <a href="{{ url_for('login') }}"> Login here</a>.</p>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html)

# -------------------------------
# Routes for Survey Templates and Details (Protected)
# -------------------------------
@app.route('/manage_templates')
@login_required
def manage_templates():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Manage Survey Catalog</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="nav">
        <p><a href="{{ url_for('home') }}">Home</a> | <a href="{{ url_for('logout') }}">Logout</a></p>
      </div>
      <h1>Manage Survey Catalog</h1>
      <p><a href="{{ url_for('create_template') }}">Create New Survey Template</a></p>
      <ul>
      {% for key, survey in catalog.items() %}
        <li>
          <strong>{{ survey.title }}</strong> (ID: {{ key }})<br>
          {{ survey.description }}<br>
          <a href="{{ url_for('survey_details', survey_type=key) }}">View Details</a> |
          <a href="{{ url_for('edit_template', survey_id=key) }}">Edit Template</a>
        </li>
      {% endfor %}
      </ul>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html, catalog=SURVEY_CATALOG)

@app.route('/survey_details/<survey_type>', methods=["GET", "POST"])
@login_required
def survey_details(survey_type):
    survey = SURVEY_CATALOG.get(survey_type)
    if not survey:
        return "Survey template not found", 404

    # Handle rating submission
    if request.method == "POST":
        try:
            rating = int(request.form.get("rating"))
            if rating < 1 or rating > 5:
                flash("Rating must be between 1 and 5.")
            else:
                # Initialize ratings if not present
                if "ratings" not in survey:
                    survey["ratings"] = []
                survey["ratings"].append(rating)
                save_catalog_to_file()
                flash("Rating submitted. Thank you!")
        except Exception as e:
            flash("Invalid rating submitted.")
        return redirect(url_for("survey_details", survey_type=survey_type))

    # Compute the average rating (default to 4 if no ratings)
    ratings = survey.get("ratings", [])
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 4

    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Survey Details: {{ survey.title }}</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="nav">
        <p>
          <a href="{{ url_for('manage_templates') }}">Back to Manage Templates</a> |
          <a href="{{ url_for('home') }}">Home</a>
        </p>
      </div>
      <h1>Survey Details: {{ survey.title }}</h1>
      <p><strong>ID:</strong> {{ survey_type }}</p>
      <p><strong>Description:</strong> {{ survey.description }}</p>
      <p><strong>Average Note:</strong> {{ avg_rating }} / 5</p>
      <h3>Questions:</h3>
      <ul>
        {% for q in survey.questions %}
          <li>
            <strong>{{ q.text }}</strong><br>
            <em>Type:</em> {{ q.type }}<br>
            {% if q.type == 'likert' %}
              <em>Options:</em> {{ q.scale }}<br>
              <em>Note:</em> {{ q.note or 'No additional note' }}
            {% endif %}
          </li>
        {% endfor %}
      </ul>
      <h3>Rate this Survey</h3>
      <form method="post">
        <label>Score (1 to 5):
          <select name="rating">
            {% for i in range(1, 6) %}
              <option value="{{ i }}">{{ i }}</option>
            {% endfor %}
          </select>
        </label>
        <button type="submit">Submit Rating</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash">
            <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
          </div>
        {% endif %}
      {% endwith %}
      <p>
        <a href="{{ url_for('customize_survey', survey_type=survey_type) }}">Customize this Survey</a>
      </p>
    </body>
    </html>
    """
    return render_template_string(html, survey=survey, survey_type=survey_type, avg_rating=avg_rating)


@app.route('/create_template', methods=['GET', 'POST'])
@login_required
def create_template():
    if request.method == 'POST':
        survey_id = request.form.get('survey_id')
        title = request.form.get('title')
        description = request.form.get('description')
        questions_str = request.form.get('questions')
        try:
            questions = json.loads(questions_str)
            if not isinstance(questions, list):
                flash("Questions must be a JSON array (list).")
                return redirect(request.url)
        except Exception as e:
            flash(f"Error parsing questions JSON: {e}")
            return redirect(request.url)
        if survey_id in SURVEY_CATALOG:
            flash("A template with that survey ID already exists. Use a different ID or edit the existing template.")
            return redirect(request.url)
        SURVEY_CATALOG[survey_id] = {
            "title": title,
            "description": description,
            "questions": questions
        }
        if save_catalog_to_file():
            flash("New survey template created successfully and saved!")
        else:
            flash("Survey template created but there was an error saving to file.")
        return redirect(url_for('manage_templates'))
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Create New Survey Template</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="nav">
        <p><a href="{{ url_for('manage_templates') }}">Back to Manage Templates</a></p>
      </div>
      <h1>Create New Survey Template</h1>
      <form method="post">
        <label>Survey ID (unique key): <input type="text" name="survey_id" required></label><br>
        <label>Title: <input type="text" name="title" required></label><br>
        <label>Description:<br>
          <textarea name="description" rows="3" cols="40" required></textarea>
        </label><br>
        <label>Questions (Enter as JSON array):<br>
          <textarea name="questions" rows="10" cols="60" required>
[
  {
    "id": "question1",
    "text": "Enter your question here",
    "type": "likert",
    "scale": [1,2,3,4,5],
    "note": "Optional note"
  }
]
          </textarea>
        </label><br>
        <button type="submit">Create Template</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/edit_template/<survey_id>', methods=['GET', 'POST'])
@login_required
def edit_template(survey_id):
    survey = SURVEY_CATALOG.get(survey_id)
    if not survey:
        return f"Survey template with id '{survey_id}' not found.", 404

    if request.method == 'POST':
        # Instead of using a fixed number, we'll iterate over provided indices.
        questions = []
        # Expecting the client to send a field "num_questions" updated by JS.
        try:
            num_questions = int(request.form.get("num_questions", 0))
        except ValueError:
            num_questions = 0

        for i in range(num_questions):
            # Only process the question if an id field is present (could have been removed).
            qid = request.form.get(f'question_{i}_id')
            if not qid:
                continue  # Skip removed or empty question fieldsets.
            text = request.form.get(f'question_{i}_text')
            qtype = request.form.get(f'question_{i}_type')
            scale = request.form.get(f'question_{i}_scale')
            note = request.form.get(f'question_{i}_note')
            if qtype == 'likert' and scale:
                scale = [s.strip() for s in scale.split(',')]
            else:
                scale = []
            questions.append({
                "id": qid,
                "text": text,
                "type": qtype,
                "scale": scale,
                "note": note
            })

        SURVEY_CATALOG[survey_id] = {
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "questions": questions
        }
        if save_catalog_to_file():
            flash("Survey template updated successfully and saved!")
        else:
            flash("Template updated but there was an error saving to file.")
        return redirect(url_for('manage_templates'))

    # GET: Render the form with existing questions and include controls to add/remove questions.
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Edit Survey Template: {{ survey.title }}</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
      <script>
        // Global counter for new question indexes.
        var questionCounter = {{ survey.questions|length }};
        function removeQuestion(elem) {
          // Remove the question fieldset from the DOM.
          var fieldset = elem.parentNode;
          fieldset.parentNode.removeChild(fieldset);
          updateNumQuestions();
        }
        function addQuestion() {
          var container = document.getElementById("questions-container");
          // Create new fieldset element.
          var fieldset = document.createElement("fieldset");
          fieldset.innerHTML = `
            <legend>New Question</legend>
            <label>ID: <input type="text" name="question_${questionCounter}_id" required></label><br>
            <label>Text: <input type="text" name="question_${questionCounter}_text" required></label><br>
            <label>Type:
              <select name="question_${questionCounter}_type">
                <option value="likert">likert</option>
                <option value="text">text</option>
              </select>
            </label><br>
            <label>Scale (comma separated, only for likert):
              <input type="text" name="question_${questionCounter}_scale">
            </label><br>
            <label>Note:
              <input type="text" name="question_${questionCounter}_note">
            </label>
            <button type="button" onclick="removeQuestion(this)">Remove this Question</button>
          `;
          container.appendChild(fieldset);
          questionCounter++;
          updateNumQuestions();
        }
        function updateNumQuestions() {
          // Update the hidden input field with the current count.
          // We count fieldset elements under the container.
          var container = document.getElementById("questions-container");
          document.getElementById("num_questions").value = container.getElementsByTagName("fieldset").length;
        }
        window.addEventListener("load", function() {
          updateNumQuestions();
        });
      </script>
    </head>
    <body>
      <div class="nav">
        <p><a href="{{ url_for('manage_templates') }}">Back to Manage Templates</a></p>
      </div>
      <h1>Edit Survey Template: {{ survey.title }}</h1>
      <form method="post">
        <label>Title: <input type="text" name="title" value="{{ survey.title }}" required></label><br>
        <label>Description:<br>
          <textarea name="description" rows="3" cols="40" required>{{ survey.description }}</textarea>
        </label><br>
        <input type="hidden" id="num_questions" name="num_questions" value="0">
        <h3>Edit Questions</h3>
        <div id="questions-container">
          {% for q in survey.questions %}
          <fieldset>
            <legend>Question {{ loop.index }}</legend>
            <label>ID: <input type="text" name="question_{{ loop.index0 }}_id" value="{{ q.id }}" required></label><br>
            <label>Text: <input type="text" name="question_{{ loop.index0 }}_text" value="{{ q.text }}" required></label><br>
            <label>Type:
              <select name="question_{{ loop.index0 }}_type">
                <option value="likert" {% if q.type == 'likert' %}selected{% endif %}>likert</option>
                <option value="text" {% if q.type == 'text' %}selected{% endif %}>text</option>
              </select>
            </label><br>
            <label>Scale (comma separated, only for likert):
              <input type="text" name="question_{{ loop.index0 }}_scale" value="{{ q.scale | join(', ') }}">
            </label><br>
            <label>Note:
              <input type="text" name="question_{{ loop.index0 }}_note" value="{{ q.note }}">
            </label>
            <button type="button" onclick="removeQuestion(this)">Remove this Question</button>
          </fieldset>
          {% endfor %}
        </div>
        <button type="button" onclick="addQuestion()">Add New Question</button><br><br>
        <button type="submit">Save Changes</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash">
            <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
          </div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html, survey=survey)


# -------------------------------
# Routes for Customized Surveys and Dashboard (Protected)
# -------------------------------
@app.route('/')
@login_required
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Home Page</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="nav">
        <p>Logged in as: {{ session['username'] }} | <a href="{{ url_for('logout') }}">Logout</a></p>
      </div>
      <h1>Home Page</h1>
      <h2>Available Survey Templates</h2>
      <ul>
      {% for key, survey in catalog.items() %}
        <li>
          <strong>{{ survey.title }}</strong>: {{ survey.description }}
          (<a href="{{ url_for('survey_details', survey_type=key) }}">View Details</a> |
           <a href="{{ url_for('customize_survey', survey_type=key) }}">Customize this survey</a>)
        </li>
      {% endfor %}
      </ul>
      <hr>
      <h2>My Customized Surveys</h2>
      {% if custom %}
        <ul>
        {% for instance_id, survey in custom.items() %}
          <li>
            <strong>{{ survey.custom_title }}</strong> - Context: {{ survey.context }}
            (<a href="{{ url_for('dashboard', instance_id=instance_id) }}">View Dashboard</a> |
             <a href="{{ url_for('view_survey', instance_id=instance_id) }}">Share Link</a>)
          </li>
        {% endfor %}
        </ul>
      {% else %}
        <p>No customized surveys created yet.</p>
      {% endif %}
      <hr>
      <p>
        <a href="{{ url_for('upload_surveys') }}">Upload Additional Survey Templates</a> |
        <a href="{{ url_for('manage_templates') }}">Manage Survey Catalog</a>
      </p>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
    </body>
    </html>
    """
    return render_template_string(html, catalog=SURVEY_CATALOG, custom=custom_surveys)

@app.route('/customize/<survey_type>', methods=['GET', 'POST'])
@login_required
def customize_survey(survey_type):
    survey = SURVEY_CATALOG.get(survey_type)
    if not survey:
        return "Survey type not found", 404
    if request.method == 'POST':
        custom_title = request.form.get('custom_title')
        context_field = request.form.get('context')
        instance_id = generate_unique_id()
        custom_surveys[instance_id] = {
            "survey_type": survey_type,
            "custom_title": custom_title,
            "context": context_field,
            "responses": []
        }
        shareable_link = url_for('view_survey', instance_id=instance_id, _external=True)
        flash(f"Survey created! Share this link with respondents: {shareable_link}")
        return redirect(url_for('dashboard', instance_id=instance_id))
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Customize Survey: {{ survey.title }}</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="nav">
        <p><a href="{{ url_for('home') }}">Back to Home</a></p>
      </div>
      <h1>Customize Survey: {{ survey.title }}</h1>
      <form method="post">
        <label>Custom Title: <input type="text" name="custom_title" required></label><br>
        <label>Context (Describe the purpose or background):<br>
            <textarea name="context" rows="3" cols="40" required></textarea>
        </label><br>
        <button type="submit">Create Custom Survey</button>
      </form>
    </body>
    </html>
    """
    return render_template_string(html, survey=survey)

@app.route('/survey/<instance_id>', methods=['GET', 'POST'])
@login_required
def view_survey(instance_id):
    survey_instance = custom_surveys.get(instance_id)
    if not survey_instance:
        return "Survey not found", 404
    survey_template = SURVEY_CATALOG.get(survey_instance["survey_type"])
    if request.method == 'POST':
        responses = {}
        for q in survey_template.get("questions", []):
            responses[q["id"]] = request.form.get(q["id"])
        score = calculate_scores(survey_instance["survey_type"], responses)
        survey_instance["responses"].append({
            "answers": responses,
            "score": score['overall']
        })
        flash("Your response has been recorded. Thank you!")
        return redirect(url_for('view_survey', instance_id=instance_id))
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>{{ survey_instance.custom_title }}</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <h1>{{ survey_instance.custom_title }}</h1>
      <p><em>{{ survey_instance.context }}</em></p>
      <form method="post">
        {% for q in survey_template.questions %}
          <div>
            <label><strong>{{ q.text }}</strong><br>
            {% if q.type == 'likert' %}
              {% for option in q.scale %}
                <input type="radio" name="{{ q.id }}" value="{{ option }}" required> {{ option }}
              {% endfor %}
              <small>{{ q.note or '' }}</small>
            {% else %}
              <textarea name="{{ q.id }}" rows="3" cols="40"></textarea>
            {% endif %}
            </label>
          </div>
          <br>
        {% endfor %}
        <button type="submit">Submit Responses</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
      <p><a href="{{ url_for('home') }}">Back to Home</a></p>
    </body>
    </html>
    """
    return render_template_string(html, survey_instance=survey_instance, survey_template=survey_template)

@app.route('/dashboard/<instance_id>')
@login_required
def dashboard(instance_id):
    survey_instance = custom_surveys.get(instance_id)
    if not survey_instance:
        return "Survey not found", 404
    num_responses = len(survey_instance["responses"])
    avg_score = sum(r["score"] for r in survey_instance["responses"]) / num_responses if num_responses else 0
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Dashboard for "{{ survey_instance.custom_title }}"</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <h1>Dashboard for "{{ survey_instance.custom_title }}"</h1>
      <p><strong>Context:</strong> {{ survey_instance.context }}</p>
      <p><strong>Number of responses:</strong> {{ num_responses }}</p>
      <p><strong>Consolidated Survey Score:</strong> {{ avg_score | round(2) }}</p>
      <h3>Individual Responses</h3>
      <ul>
        {% for resp in survey_instance.responses %}
          <li>Score: {{ resp.score }} - Answers: {{ resp.answers }}</li>
        {% endfor %}
      </ul>
      <p>
        <a href="{{ url_for('view_survey', instance_id=instance_id) }}">Share Survey Link</a>
      </p>
      <form method="post" action="{{ url_for('export_report', instance_id=instance_id) }}">
        <button type="submit">Save Report to File</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
      <p><a href="{{ url_for('home') }}">Back to Home</a></p>
    </body>
    </html>
    """
    return render_template_string(html, survey_instance=survey_instance, num_responses=num_responses, avg_score=avg_score, instance_id=instance_id)

@app.route('/export_report/<instance_id>', methods=['POST'])
@login_required
def export_report(instance_id):
    survey_instance = custom_surveys.get(instance_id)
    if not survey_instance:
        return "Survey not found", 404
    num_responses = len(survey_instance["responses"])
    avg_score = sum(r["score"] for r in survey_instance["responses"]) / num_responses if num_responses else 0
    report_data = {
        "custom_title": survey_instance["custom_title"],
        "context": survey_instance["context"],
        "num_responses": num_responses,
        "avg_score": avg_score,
        "responses": survey_instance["responses"]
    }
    filename = save_report_to_file(instance_id, report_data)
    flash(f"Report saved to file: {filename}")
    return redirect(url_for('dashboard', instance_id=instance_id))

@app.route('/upload_surveys', methods=['GET', 'POST'])
@login_required
def upload_surveys():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part provided")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)
        try:
            data = json.load(file)
            SURVEY_CATALOG.update(data)
            if save_catalog_to_file():
                flash("Surveys loaded and catalog file updated successfully!")
            else:
                flash("Surveys loaded but there was an error saving to file.")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Error loading file: {e}")
            return redirect(request.url)
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Upload Survey Templates</title>
      <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <h1>Upload Survey Templates</h1>
      <form method="post" enctype="multipart/form-data">
        <label>Select JSON File: <input type="file" name="file" accept=".json" required></label>
        <button type="submit">Upload</button>
      </form>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash"><ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul></div>
        {% endif %}
      {% endwith %}
      <p><a href="{{ url_for('home') }}">Back to Home</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/reports/<path:filename>')
@login_required
def download_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

# -------------------------------
# Run the App
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
