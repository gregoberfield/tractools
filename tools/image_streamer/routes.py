from flask import Blueprint, jsonify, request, render_template
from .service import ImageStreamerTool
import logging

logger = logging.getLogger(__name__)
image_streamer_bp = Blueprint('image_streamer', __name__)

# Global service instance
_service = None

def get_service():
    """Get or create the image streamer service instance"""
    global _service
    if _service is None:
        _service = ImageStreamerTool()
        _service.start()
    return _service

@image_streamer_bp.route('/status')
def get_status():
    """Get status of all streams"""
    try:
        service = get_service()
        status_data = service.get_status()
        
        # Return JSON for API calls, HTML for browser requests
        if request.headers.get('Accept') == 'application/json':
            return jsonify(status_data)
        else:
            return render_template('tools/image_streamer/status.html')
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('tools/image_streamer/status.html', error=str(e))

@image_streamer_bp.route('/streams')
def list_streams():
    """List all configured streams"""
    try:
        service = get_service()
        streams_data = service.list_streams()
        
        # Return JSON for API calls, HTML for browser requests
        if request.headers.get('Accept') == 'application/json':
            return jsonify(streams_data)
        else:
            return render_template('tools/image_streamer/streams.html', streams=streams_data['streams'])
    except Exception as e:
        logger.error(f"Error listing streams: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('tools/image_streamer/streams.html', error=str(e), streams=[])

@image_streamer_bp.route('/streams/<stream_name>/start', methods=['POST'])
def start_stream(stream_name):
    """Start a specific stream"""
    try:
        service = get_service()
        result = service.start_stream(stream_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting stream {stream_name}: {e}")
        return jsonify({'error': str(e)}), 500

@image_streamer_bp.route('/streams/<stream_name>/stop', methods=['POST'])
def stop_stream(stream_name):
    """Stop a specific stream"""
    try:
        service = get_service()
        result = service.stop_stream(stream_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping stream {stream_name}: {e}")
        return jsonify({'error': str(e)}), 500

@image_streamer_bp.route('/reload', methods=['POST'])
def reload_config():
    """Reload configuration file"""
    try:
        service = get_service()
        result = service.reload_config()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        return jsonify({'error': str(e)}), 500