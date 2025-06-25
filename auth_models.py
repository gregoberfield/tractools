"""
Authentication models for TRACTools.
"""

from tools.weather.models import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_admin_user(username):
        """Get admin user by username."""
        return User.query.filter_by(username=username, is_admin=True).first()
    
    @staticmethod
    def create_default_admin():
        """Create default admin user if none exists."""
        if User.query.filter_by(is_admin=True).first():
            return None  # Admin already exists
        
        from config import Config
        admin = User(
            username=Config.ADMIN_USERNAME,
            is_admin=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        
        db.session.add(admin)
        db.session.commit()
        
        logger.info(f"Created default admin user: {admin.username}")
        return admin
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }