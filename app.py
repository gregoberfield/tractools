# app.py - Main Flask Application
from flask import Flask, jsonify, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import logging
import os
from tools.image_streamer import ImageStreamerTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        
        logger = logging.getLogger(__name__)
        
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
            
            # Return appropriate status code based on result
            if result['status'] == 'error':
                return jsonify(result), 400
            else:
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
