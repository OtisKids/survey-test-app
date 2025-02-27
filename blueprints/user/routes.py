from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import load_users, save_users, check_password_hash, generate_password_hash

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        users = load_users()
        if username in users:
            stored_hash = users[username]['password']
            if check_password_hash(stored_hash, password):
                session['username'] = username
                flash("Logged in successfully!", "success")
                return redirect(url_for('user.dashboard'))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("User not found.", "error")
        return redirect(url_for('user.login'))
    return render_template('login.html')

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        users = load_users()
        if username in users:
            flash("Username already exists.", "error")
            return redirect(url_for('user.register'))
        if password!= confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('user.register'))
        hashed = generate_password_hash(password)
        users[username] = {'password': hashed}
        save_users(users)
        flash("Registered successfully. Please log in.", "success")
        return redirect(url_for('user.login'))
    return render_template('register.html')

@user_bp.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('user.login'))




@user_bp.route('/user/info')
def user_info():
    """
    User info route.

    Replace with actual logic to fetch user personal information.
    """
    user_info = {'username': session.get('username', 'User'), 'email': 'user@example.com'}
    return render_template("user_info.html", user=user_info)

@user_bp.route('/user/billing')
def user_billing():
    """
    User billing route.

    Replace with actual logic to fetch billing/plans data.
    """
    plans = [
        {'name': 'Free', 'features': 'Basic features'},
        {'name': 'Premium', 'features': 'Advanced features and priority support'}
    ]
    return render_template("user_billing.html", plans=plans)
