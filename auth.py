"""
Authentication module for TRACTools admin functionality.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import logging

logger = logging.getLogger(__name__)

# Database User class for admin authentication
class AdminUser(UserMixin):
    def __init__(self, user_model):
        self.id = str(user_model.id)
        self.username = user_model.username
        self.is_admin = user_model.is_admin
        self._user_model = user_model

    @staticmethod
    def get(user_id):
        """Get user by ID"""
        from auth_models import User
        user = User.query.get(int(user_id))
        if user and user.is_admin:
            return AdminUser(user)
        return None

    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        from auth_models import User
        user = User.get_admin_user(username)
        if user:
            return AdminUser(user)
        return None

    @staticmethod
    def verify_password(username, password):
        """Verify admin credentials against database"""
        from auth_models import User
        user = User.get_admin_user(username)
        if user and user.check_password(password):
            user.update_last_login()
            return True
        return False

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    flash('You need to be logged in as an administrator to access this page.', 'warning')
    return redirect(url_for('auth.login', next=request.url))

def init_auth(app):
    """Initialize authentication for the Flask app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

def is_admin():
    """Check if current user is an admin"""
    return current_user.is_authenticated and getattr(current_user, 'is_admin', False)