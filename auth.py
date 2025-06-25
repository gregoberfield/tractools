"""
Authentication module for TRACTools admin functionality.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
import logging

logger = logging.getLogger(__name__)

# Simple User class for admin authentication
class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
        self.is_admin = True

    @staticmethod
    def get(username):
        """Get user by username - only returns admin user if credentials match"""
        if username == Config.ADMIN_USERNAME:
            return AdminUser(username)
        return None

    @staticmethod
    def verify_password(username, password):
        """Verify admin credentials"""
        return (username == Config.ADMIN_USERNAME and 
                password == Config.ADMIN_PASSWORD)

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