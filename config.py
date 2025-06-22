import os
import json

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    CONFIG_FILE = os.environ.get('CONFIG_FILE') or 'config/streams.json'
    RTSP_BASE_PORT = int(os.environ.get('RTSP_BASE_PORT', 8554))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # RTSP Authentication
    RTSP_PUBLISHER_USER = os.environ.get('RTSP_PUBLISHER_USER', 'publisher')
    RTSP_PUBLISHER_PASS = os.environ.get('RTSP_PUBLISHER_PASS', 'stream123')
    RTSP_VIEWER_USER = os.environ.get('RTSP_VIEWER_USER', 'viewer')
    RTSP_VIEWER_PASS = os.environ.get('RTSP_VIEWER_PASS', 'viewer')
    
    @staticmethod
    def load_streams_config():
        """Load stream configuration from JSON file"""
        config_path = Config.CONFIG_FILE
        if not os.path.exists(config_path):
            # Create default config if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            default_config = {
                "streams": [
                    {
                        "name": "sample_stream",
                        "url": "https://picsum.photos/640/480",
                        "update_frequency": 5,
                        "enabled": True
                    }
                ]
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f"Invalid configuration file: {e}")