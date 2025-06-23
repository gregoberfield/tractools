from flask import Blueprint, jsonify, request, render_template
from .service import RoofStatusTool
import logging

logger = logging.getLogger(__name__)
roof_status_bp = Blueprint('roof_status', __name__)

# Global service instance
_service = None

def get_service():
    """Get or create the roof status service instance"""
    global _service
    if _service is None:
        _service = RoofStatusTool()
        _service.start()
    return _service

@roof_status_bp.route('/status')
def get_status():
    """Get status page showing all roof statuses"""
    try:
        service = get_service()
        status_data = service.get_all_statuses()
        summary_stats = service.get_summary_stats()
        
        # Return JSON for API calls, HTML for browser requests
        if request.headers.get('Accept') == 'application/json':
            return jsonify({**status_data, 'summary': summary_stats})
        else:
            return render_template('tools/roof_status/status.html', 
                                 status_data=status_data, 
                                 summary_stats=summary_stats)
    except Exception as e:
        logger.error(f"Error getting roof status: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('tools/roof_status/status.html', 
                                 error=str(e), 
                                 status_data={'statuses': {}}, 
                                 summary_stats={'total_buildings': 0})

@roof_status_bp.route('/building/<building_id>')
def get_building_status(building_id):
    """Get status for a specific building"""
    try:
        service = get_service()
        building_data = service.get_building_status(building_id)
        
        if not building_data:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Building not found'}), 404
            else:
                return render_template('tools/roof_status/building.html', 
                                     error='Building not found', 
                                     building_id=building_id)
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify(building_data)
        else:
            return render_template('tools/roof_status/building.html', 
                                 building_data=building_data)
    except Exception as e:
        logger.error(f"Error getting building status for {building_id}: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('tools/roof_status/building.html', 
                                 error=str(e), 
                                 building_id=building_id)

# API endpoint for external submissions
@roof_status_bp.route('/api/sfro-roof-status', methods=['POST'])
def update_roof_status():
    """API endpoint to receive roof status updates"""
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
        
        # Process the update
        service = get_service()
        result = service.update_roof_status(data['file_path'], data['found'])
        
        # Return appropriate status code based on result
        if result['status'] == 'error':
            return jsonify(result), 400
        else:
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error processing roof status update: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@roof_status_bp.route('/api/status')
def api_get_all_statuses():
    """API endpoint to get all roof statuses"""
    try:
        service = get_service()
        status_data = service.get_all_statuses()
        summary_stats = service.get_summary_stats()
        
        return jsonify({**status_data, 'summary': summary_stats})
    except Exception as e:
        logger.error(f"Error getting all statuses via API: {e}")
        return jsonify({'error': str(e)}), 500

@roof_status_bp.route('/api/building/<building_id>')
def api_get_building_status(building_id):
    """API endpoint to get status for a specific building"""
    try:
        service = get_service()
        building_data = service.get_building_status(building_id)
        
        if not building_data:
            return jsonify({'error': 'Building not found'}), 404
            
        return jsonify(building_data)
    except Exception as e:
        logger.error(f"Error getting building status via API for {building_id}: {e}")
        return jsonify({'error': str(e)}), 500

@roof_status_bp.route('/api/debug')
def api_debug():
    """Debug endpoint to show raw data and file info"""
    try:
        service = get_service()
        import os
        
        debug_info = {
            'data_file_path': service.data_file,
            'data_file_exists': os.path.exists(service.data_file),
            'data_file_size': os.path.getsize(service.data_file) if os.path.exists(service.data_file) else 0,
            'in_memory_count': len(service.roof_statuses),
            'in_memory_keys': list(service.roof_statuses.keys()),
            'service_running': service.running
        }
        
        # Try to read the file directly
        if os.path.exists(service.data_file):
            try:
                with open(service.data_file, 'r') as f:
                    file_content = f.read()
                    debug_info['file_content_preview'] = file_content[:500] + '...' if len(file_content) > 500 else file_content
            except Exception as e:
                debug_info['file_read_error'] = str(e)
        
        return jsonify(debug_info)
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({'error': str(e)}), 500
