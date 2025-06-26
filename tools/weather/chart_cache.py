"""
Chart caching system for weather data images.
Caches generated chart images for a specified duration to improve performance.
"""

import time
import hashlib
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChartCache:
    """Simple in-memory cache for chart images."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """Initialize the cache with default TTL in seconds."""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_cache_key(self, chart_type: str, historical_data: list, astronomical_zones: list) -> str:
        """Generate a unique cache key based on chart type and data."""
        # Create a hash of the data to use as cache key
        data_for_hash = {
            'chart_type': chart_type,
            'data_count': len(historical_data),
            'data_hash': self._hash_data(historical_data),
            'zones_hash': self._hash_data(astronomical_zones)
        }
        
        # Create hash of the combined data
        key_string = json.dumps(data_for_hash, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _hash_data(self, data: list) -> str:
        """Create a hash of data for cache key generation."""
        if not data:
            return "empty"
        
        # For historical data, hash based on first/last timestamps and count
        if isinstance(data, list) and data:
            if isinstance(data[0], dict) and 'created_at' in data[0]:
                # Historical weather data
                hash_data = {
                    'count': len(data),
                    'first': data[0].get('created_at', ''),
                    'last': data[-1].get('created_at', ''),
                    'sample_temp': data[0].get('temperature_f', 0) if data else 0
                }
            else:
                # Astronomical zones
                hash_data = {
                    'count': len(data),
                    'first': data[0].get('timestamp', 0) if data else 0,
                    'last': data[-1].get('timestamp', 0) if data else 0
                }
            
            return hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()[:8]
        
        return "empty"
    
    def get(self, chart_type: str, historical_data: list, astronomical_zones: list) -> Optional[str]:
        """Get cached chart image if available and not expired."""
        cache_key = self._generate_cache_key(chart_type, historical_data, astronomical_zones)
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # Check if cache entry has expired
            if time.time() < cache_entry['expires_at']:
                logger.debug(f"Cache hit for {chart_type} chart (key: {cache_key[:8]}...)")
                return cache_entry['image_data']
            else:
                # Remove expired entry
                logger.debug(f"Cache expired for {chart_type} chart (key: {cache_key[:8]}...)")
                del self.cache[cache_key]
        
        logger.debug(f"Cache miss for {chart_type} chart (key: {cache_key[:8]}...)")
        return None
    
    def set(self, chart_type: str, historical_data: list, astronomical_zones: list, 
            image_data: str, ttl: Optional[int] = None) -> None:
        """Store chart image in cache with TTL."""
        if not image_data:
            return
        
        cache_key = self._generate_cache_key(chart_type, historical_data, astronomical_zones)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        self.cache[cache_key] = {
            'image_data': image_data,
            'created_at': time.time(),
            'expires_at': expires_at,
            'chart_type': chart_type
        }
        
        logger.debug(f"Cached {chart_type} chart (key: {cache_key[:8]}..., expires in {ttl or self.default_ttl}s)")
    
    def clear_expired(self) -> int:
        """Remove all expired cache entries. Returns number of entries removed."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() 
            if current_time >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def clear_all(self) -> int:
        """Clear all cache entries. Returns number of entries removed."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared all {count} cache entries")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        active_entries = sum(1 for entry in self.cache.values() if current_time < entry['expires_at'])
        expired_entries = len(self.cache) - active_entries
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_size_mb': sum(len(entry['image_data']) for entry in self.cache.values()) / (1024 * 1024)
        }

# Global cache instance
_chart_cache = None

def get_chart_cache() -> ChartCache:
    """Get the global chart cache instance."""
    global _chart_cache
    if _chart_cache is None:
        _chart_cache = ChartCache(default_ttl=300)  # 5 minutes
    return _chart_cache