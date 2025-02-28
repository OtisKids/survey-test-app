# helpers/auth_helpers.py
import re
from flask import flash

def validate_login(email, password):
    """
    Validate login credentials format
    
    Args:
        email (str): Email address
        password (str): Password
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    if not email or not password:
        flash('Email and password are required', 'error')
        return False
        
    # Basic email format validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('Please enter a valid email address', 'error')
        return False
        
    return True

def validate_registration(name, email, password, confirm_password):
    """
    Validate registration form data
    
    Args:
        name (str): User's name
        email (str): Email address
        password (str): Password
        confirm_password (str): Password confirmation
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    if not name or not email or not password or not confirm_password:
        flash('All fields are required', 'error')
        return False
        
    # Basic email format validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('Please enter a valid email address', 'error')
        return False
        
    # Password length check
    if len(password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return False
        
    # Password confirmation check
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return False
        
    return True