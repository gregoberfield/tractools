#!/var/www/tools/tractools/venv/bin/python3
import sys
import os
import site

# Path to the virtual environment
venv_path = '/var/www/tools/tractools/.venv'

# Add the virtual environment's site-packages to Python path
# This replaces the deprecated activate_this.py approach
venv_site_packages = os.path.join(venv_path, 'lib', 'python{}.{}'.format(
    sys.version_info.major, sys.version_info.minor), 'site-packages')

if os.path.exists(venv_site_packages):
    site.addsitedir(venv_site_packages)

# Add your project directory to the sys.path
project_path = "/var/www/tools/tractools"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

# Change to the application directory to ensure relative paths work correctly
os.chdir(project_path)

try:
    # Import the Flask application
    from app import app as application
except ImportError as e:
    # Log the error for debugging
    import traceback
    with open('/var/log/apache2/tractools_import_error.log', 'a') as f:
        f.write(f"Import error: {e}\n")
        f.write(f"Python path: {sys.path}\n")
        f.write(f"Traceback: {traceback.format_exc()}\n")
    raise

if __name__ == "__main__":
    application.run()