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
    
    return app

# For direct execution (development)
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
