# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-dev-key-do-not-use-in-production')
    USERS_FILE = os.environ.get('USERS_FILE', 'users.json')
    CATALOG_FILE = os.environ.get('CATALOG_FILE', 'survey_catalog.json')
    SURVEYS_FILE = os.environ.get('SURVEYS_FILE', 'surveys.json')
    RESPONSES_FILE = os.environ.get('RESPONSES_FILE', 'responses.json')
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Additional app settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # You can override any Config settings here

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use test-specific files
    USERS_FILE = 'test_users.json'
    CATALOG_FILE = 'test_catalog.json'
    SURVEYS_FILE = 'test_surveys.json'
    RESPONSES_FILE = 'test_responses.json'

class ProductionConfig(Config):
    """Production configuration"""
    # No overrides needed - use base config

# Dictionary of configuration environments
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}