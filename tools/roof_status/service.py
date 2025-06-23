import threading
import re
import json
import os
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
        self.data_file = 'logs/roof_status_data.json'
        
    def start(self):
        """Start the roof status service"""
        logger.info("Starting Roof Status Tool")
        self.running = True
        self._load_data()
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
                'status': 'open' if found else 'closed',
                'status_display': 'OPEN' if found else 'CLOSED'
            }
            
        logger.info(f"Updated roof status for {building_id}: {'found' if found else 'not found'}")
        
        # Save data to file after update
        self._save_data()
        
        return {
            'status': 'success',
            'message': f'Updated status for {building_id}',
            'building_id': building_id,
            'data': self.roof_statuses[building_id]
        }
        
    def get_all_statuses(self) -> Dict[str, Any]:
        """Get all roof statuses"""
        # Reload data from disk to ensure we have the latest data
        self._load_data()
        
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
            open_count = sum(1 for status in self.roof_statuses.values() if status['found'])
            closed_count = total - open_count
            
            return {
                'total_buildings': total,
                'open_count': open_count,
                'closed_count': closed_count,
                'open_percentage': round((open_count / total * 100) if total > 0 else 0, 1),
                # Keep legacy fields for backward compatibility
                'found_count': open_count,
                'not_found_count': closed_count,
                'found_percentage': round((open_count / total * 100) if total > 0 else 0, 1)
            }
    
    def _load_data(self):
        """Load roof status data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.roof_statuses = data.get('roof_statuses', {})
                    logger.info(f"Loaded {len(self.roof_statuses)} roof status entries from {self.data_file}")
            else:
                logger.info(f"No existing data file found at {self.data_file}, starting with empty data")
        except Exception as e:
            logger.error(f"Error loading data from {self.data_file}: {e}")
            self.roof_statuses = {}
    
    def _save_data(self):
        """Save roof status data to file"""
        try:
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            data = {
                'roof_statuses': self.roof_statuses,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.roof_statuses)} roof status entries to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving data to {self.data_file}: {e}")
