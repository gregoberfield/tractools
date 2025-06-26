# app.py - Main Flask Application
from flask import Flask, jsonify, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import logging
import os
from tools.image_streamer import ImageStreamerTool

# Configure logging
import logging.handlers

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)

# Create specific logger for API requests
api_logger = logging.getLogger('api_requests')
api_logger.setLevel(logging.INFO)
api_logger.propagate = False  # Don't propagate to root logger

api_handler = logging.handlers.RotatingFileHandler(
    'logs/api_requests.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
api_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
api_logger.addHandler(api_handler)

# Also add console handler for API logger during development
api_console_handler = logging.StreamHandler()
api_console_handler.setFormatter(logging.Formatter('API: %(asctime)s - %(levelname)s - %(message)s'))
api_logger.addHandler(api_console_handler)

logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')
    
    # Ensure instance directory exists
    import os
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Set the database URI from the property
    from config import Config
    config_instance = Config()
    app.config['SQLALCHEMY_DATABASE_URI'] = config_instance.SQLALCHEMY_DATABASE_URI
    
    # Initialize authentication
    from auth import init_auth
    init_auth(app)
    
    # Initialize database
    from tools.weather.models import db
    db.init_app(app)
    
    # Import auth models to register them with SQLAlchemy
    from auth_models import User
    
    # Initialize Flask-Migrate
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    # Register a CLI command to initialize the database
    @app.cli.command()
    def init_db():
        """Initialize the database with tables and default admin user."""
        db.create_all()
        User.create_default_admin()
        print("Database initialized successfully!")
    
    # Only initialize database for non-CLI contexts
    if not app.config.get('TESTING', False):
        try:
            with app.app_context():
                # Check if we need to initialize (only if no tables exist)
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                existing_tables = inspector.get_table_names()
                
                if not existing_tables:
                    logger.info("No tables found, creating initial database...")
                    db.create_all()
                    User.create_default_admin()
        except Exception as e:
            # Don't fail app startup if database isn't accessible yet
            logger.warning(f"Database initialization skipped: {e}")
    
    # Register authentication blueprint
    from auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Import module manager and create error handlers
    from module_manager import create_module_error_handlers, ModuleManager
    create_module_error_handlers(app)
    
    # Make module status available to all templates
    @app.context_processor
    def inject_module_status():
        return dict(module_manager=ModuleManager)
    
    # Register tool blueprints conditionally based on module configuration
    if ModuleManager.is_module_enabled('image_streamer'):
        from tools.image_streamer import image_streamer_bp
        app.register_blueprint(image_streamer_bp, url_prefix='/tools/image-streamer')
        logger.info("Image Streamer module registered")
    else:
        logger.info("Image Streamer module disabled")
    
    if ModuleManager.is_module_enabled('roof_status'):
        from tools.roof_status import roof_status_bp
        app.register_blueprint(roof_status_bp, url_prefix='/tools/roof-status')
        logger.info("Roof Status module registered")
    else:
        logger.info("Roof Status module disabled")
    
    if ModuleManager.is_module_enabled('weather'):
        from tools.weather import weather_bp
        app.register_blueprint(weather_bp, url_prefix='/tools/weather')
        logger.info("Weather module registered")
    else:
        logger.info("Weather module disabled")
    
    # Main application routes
    @app.route('/')
    def index():
        """Main dashboard showing available tools"""
        modules_status = ModuleManager.get_all_modules_status()
        return render_template('index.html', modules=modules_status)
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers"""
        return jsonify({
            'status': 'healthy',
            'tools': ['image-streamer', 'roof-status', 'weather']
        })
    
    # Root-level API endpoint for external access
    @app.route('/api/sfro-roof-status', methods=['POST'])
    def root_api_sfro_roof_status():
        """Root-level API endpoint that forwards to the roof status tool"""
        # Check if roof status module is enabled
        if not ModuleManager.is_module_enabled('roof_status'):
            return jsonify({
                'status': 'error',
                'message': 'Roof status module is currently disabled'
            }), 503
            
        from tools.roof_status.routes import get_service
        from flask import request
        import logging
        import json
        
        logger = logging.getLogger(__name__)
        
        # Log only essential request details for performance
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # Only log on debug level to reduce I/O overhead
        logger.debug(f"API Request from IP: {client_ip}")
        
        try:
            
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json()
            
            # Validate required fields
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No JSON data provided'
                }), 400
                
            if 'file_path' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required field: file_path'
                }), 400
                
            if 'found' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required field: found'
                }), 400
            
            # Validate data types
            if not isinstance(data['file_path'], str):
                return jsonify({
                    'status': 'error',
                    'message': 'file_path must be a string'
                }), 400
                
            if not isinstance(data['found'], bool):
                return jsonify({
                    'status': 'error',
                    'message': 'found must be a boolean'
                }), 400
            
            # Process the update using the roof status service
            service = get_service()
            result = service.update_roof_status(data['file_path'], data['found'])
            
            # Return appropriate status code based on result (reduced logging)
            if result['status'] == 'error':
                logger.error(f"API Error: {result.get('message', 'Unknown error')}")
                return jsonify(result), 400
            else:
                logger.debug(f"API Success: Building {result.get('building_id', 'unknown')}")
                return jsonify(result), 200
                
        except Exception as e:
            logger.error(f"Error processing roof status update at root API: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    return app

# Create app instance for Flask CLI
app = create_app()

# For direct execution (development)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
