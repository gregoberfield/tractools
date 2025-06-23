import threading
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RoofStatusTool:
    """Service for managing roof status data from API submissions"""
    
    def __init__(self):
        self.roof_statuses: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.running = False
        
    def start(self):
        """Start the roof status service"""
        logger.info("Starting Roof Status Tool")
        self.running = True
        return True
        
    def stop(self):
        """Stop the roof status service"""
        logger.info("Stopping Roof Status Tool")
        self.running = False
        
    def extract_building_id(self, file_path: str) -> Optional[str]:
        """Extract building identifier from file path"""
        # Look for pattern like "building-1", "building-2", etc.
        match = re.search(r'building-(\w+)', file_path, re.IGNORECASE)
        if match:
            return f"building-{match.group(1)}"
        
        # Fallback: try to extract any identifier between path separators
        # This handles cases like "R:\roof\site-a\file.txt" -> "site-a"
        parts = file_path.replace('\\', '/').split('/')
        for part in parts:
            if part and part.lower() != 'roof' and not part.endswith('.txt'):
                # Skip drive letters and common directory names
                if not (len(part) == 2 and part.endswith(':')):
                    return part
        
        return None
        
    def update_roof_status(self, file_path: str, found: bool) -> Dict[str, Any]:
        """Update roof status for a building based on API submission"""
        building_id = self.extract_building_id(file_path)
        
        if not building_id:
            logger.warning(f"Could not extract building ID from path: {file_path}")
            return {
                'status': 'error',
                'message': 'Could not extract building identifier from file path'
            }
        
        timestamp = datetime.now()
        
        with self.lock:
            self.roof_statuses[building_id] = {
                'building_id': building_id,
                'file_path': file_path,
                'found': found,
                'last_updated': timestamp.isoformat(),
                'last_updated_display': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'found' if found else 'not_found'
            }
            
        logger.info(f"Updated roof status for {building_id}: {'found' if found else 'not found'}")
        
        return {
            'status': 'success',
            'message': f'Updated status for {building_id}',
            'building_id': building_id,
            'data': self.roof_statuses[building_id]
        }
        
    def get_all_statuses(self) -> Dict[str, Any]:
        """Get all roof statuses"""
        with self.lock:
            return {
                'service_running': self.running,
                'total_buildings': len(self.roof_statuses),
                'last_update': max([status['last_updated'] for status in self.roof_statuses.values()]) if self.roof_statuses else None,
                'statuses': dict(self.roof_statuses)
            }
            
    def get_building_status(self, building_id: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific building"""
        with self.lock:
            return self.roof_statuses.get(building_id)
            
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        with self.lock:
            total = len(self.roof_statuses)
            found_count = sum(1 for status in self.roof_statuses.values() if status['found'])
            not_found_count = total - found_count
            
            return {
                'total_buildings': total,
                'found_count': found_count,
                'not_found_count': not_found_count,
                'found_percentage': round((found_count / total * 100) if total > 0 else 0, 1)
            }
