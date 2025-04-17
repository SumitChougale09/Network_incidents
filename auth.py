from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('incident.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_user_by_username(username)
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('incident.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('incident.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Simple validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.get_user_by_username(username):
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.get_user_by_email(email):
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        # Create user
        user = User.create_user(username, email, password, 'support_engineer')
        
        # Log in the user
        login_user(user)
        
        flash('Registration successful', 'success')
        return redirect(url_for('incident.dashboard'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email')
    
    # Update email
    if email and email != current_user.email:
        if User.get_user_by_email(email):
            flash('Email already exists', 'danger')
        else:
            current_user.email = email
            flash('Profile updated successfully', 'success')
    
    # Change password
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if current_password and new_password:
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'danger')
        else:
            current_user.set_password(new_password)
            flash('Password changed successfully', 'success')
    
    return redirect(url_for('auth.profile'))
