# blueprints/survey/__init__.py
from flask import Blueprint

survey_bp = Blueprint('survey', __name__, template_folder='../../templates')

from blueprints.survey.routes import *