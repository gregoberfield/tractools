#!/var/www/tools/tractools/venv/bin/python3
import sys
import os

# Add project directory to Python path
sys.path.insert(0, '/var/www/tools/tractools')

# Change to application directory
os.chdir('/var/www/tools/tractools')

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Ensure instance directory exists for database
os.makedirs('instance', exist_ok=True)

# Import the Flask application
from app import create_app
application = create_app()

if __name__ == "__main__":
    application.run()