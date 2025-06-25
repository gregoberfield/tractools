"""
Module management system for TRACTools.
Handles enabling/disabling of tool modules.
"""

from flask import current_app, abort, flash, redirect, url_for
from functools import wraps
from config import Config

class ModuleManager:
    """Manages module states and access control."""
    
    @staticmethod
    def is_module_enabled(module_name: str) -> bool:
        """Check if a module is enabled."""
        return Config.MODULES_ENABLED.get(module_name, False)
    
    @staticmethod
    def get_module_status(module_name: str) -> dict:
        """Get module status information."""
        enabled = ModuleManager.is_module_enabled(module_name)
        return {
            'name': module_name,
            'enabled': enabled,
            'status': 'Active' if enabled else 'Inactive',
            'badge_class': 'bg-success' if enabled else 'bg-secondary'
        }
    
    @staticmethod
    def get_all_modules_status() -> dict:
        """Get status of all modules."""
        modules = {}
        for module_name in Config.MODULES_ENABLED.keys():
            modules[module_name] = ModuleManager.get_module_status(module_name)
        return modules
    
    @staticmethod
    def require_module_enabled(module_name: str):
        """Decorator to require module to be enabled."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not ModuleManager.is_module_enabled(module_name):
                    abort(503)  # Service Unavailable
                return f(*args, **kwargs)
            return decorated_function
        return decorator

def create_module_error_handlers(app):
    """Create error handlers for disabled modules."""
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle service unavailable errors for disabled modules."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Service Unavailable - TRACTools</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                                <h2 class="mt-3">Service Unavailable</h2>
                                <p class="text-muted">This module is currently disabled by the administrator.</p>
                                <a href="/" class="btn btn-primary">Return to Dashboard</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
        </body>
        </html>
        """, 503