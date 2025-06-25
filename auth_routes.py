"""
Authentication routes for TRACTools admin functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from auth import AdminUser
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if AdminUser.verify_password(username, password):
            user = AdminUser.get_by_username(username)
            login_user(user)
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout current admin user"""
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/modules')
@login_required
def manage_modules():
    """Admin page to manage module states"""
    from module_manager import ModuleManager
    modules_status = ModuleManager.get_all_modules_status()
    return render_template('auth/modules.html', modules=modules_status)