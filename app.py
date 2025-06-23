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
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Register tool blueprints
    from tools.image_streamer import image_streamer_bp
    from tools.roof_status import roof_status_bp
    app.register_blueprint(image_streamer_bp, url_prefix='/tools/image-streamer')
    app.register_blueprint(roof_status_bp, url_prefix='/tools/roof-status')
    
    # Main application routes
    @app.route('/')
    def index():
        """Main dashboard showing available tools"""
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers"""
        return jsonify({
            'status': 'healthy',
            'tools': ['image-streamer', 'roof-status']
        })
    
    # Root-level API endpoint for external access
    @app.route('/api/sfro-roof-status', methods=['POST'])
    def root_api_sfro_roof_status():
        """Root-level API endpoint that forwards to the roof status tool"""
        from tools.roof_status.routes import get_service
        from flask import request
        import logging
        import json
        
        logger = logging.getLogger(__name__)
        
        # Log the incoming request details
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        user_agent = request.headers.get('User-Agent', 'unknown')
        content_type = request.headers.get('Content-Type', 'unknown')
        
        api_logger.info(f"API Request - IP: {client_ip}, User-Agent: {user_agent}, Content-Type: {content_type}")
        
        try:
            # Get raw request data for logging
            raw_data = request.get_data(as_text=True)
            api_logger.info(f"API Request Body: {raw_data}")
            
            # Validate request content type
            if not request.is_json:
                api_logger.warning(f"Invalid content type: {content_type}")
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
            
            # Log the processing result
            api_logger.info(f"API Processing Result: {json.dumps(result)}")
            
            # Return appropriate status code based on result
            if result['status'] == 'error':
                api_logger.error(f"API Error Response: {json.dumps(result)}")
                return jsonify(result), 400
            else:
                api_logger.info(f"API Success Response: Building {result.get('building_id', 'unknown')} - Status: {'found' if data['found'] else 'not_found'}")
                return jsonify(result), 200
                
        except Exception as e:
            logger.error(f"Error processing roof status update at root API: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    return app

# For direct execution (development)
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
