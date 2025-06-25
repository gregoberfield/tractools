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
    
    # Database Configuration
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')  # sqlite, postgresql, mysql
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # SQLite (default)
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', 'weather_data.db')
    
    # PostgreSQL
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'weather_db')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
    
    # MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_DB = os.environ.get('MYSQL_DB', 'weather_db')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Generate SQLAlchemy database URI based on configuration"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.DATABASE_TYPE.lower() == 'postgresql':
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        elif self.DATABASE_TYPE.lower() == 'mysql':
            return f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        else:
            # Default to SQLite
            return f"sqlite:///{self.SQLITE_DB_PATH}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Observatory Location Configuration for astronomical calculations
    OBSERVATORY_LATITUDE = float(os.environ.get('OBSERVATORY_LATITUDE', 0.0))
    OBSERVATORY_LONGITUDE = float(os.environ.get('OBSERVATORY_LONGITUDE', 0.0))
    OBSERVATORY_ELEVATION = float(os.environ.get('OBSERVATORY_ELEVATION', 0.0))  # meters above sea level
    OBSERVATORY_TIMEZONE = os.environ.get('OBSERVATORY_TIMEZONE', 'UTC')
    
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