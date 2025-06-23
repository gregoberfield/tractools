#!/var/www/tools/tractools/venv/bin/python3
import sys
import os

# Add project directory to Python path
sys.path.insert(0, '/var/www/tools/tractools')
os.chdir('/var/www/tools/tractools')
os.environ['FLASK_ENV'] = 'production'

# Debug function to write to a writable location
def debug_log(message):
    try:
        with open('/var/www/tools/tractools/debug.log', 'a') as f:
            f.write(f"{message}\n")
    except:
        pass

try:
    # Import the app module first
    import app
    debug_log(f"App module imported successfully")
    debug_log(f"Available attributes in app: {dir(app)}")
    
    # Try different common Flask app names
    if hasattr(app, 'app'):
        application = app.app
        debug_log("Found Flask app as 'app.app'")
    elif hasattr(app, 'application'):
        application = app.application
        debug_log("Found Flask app as 'app.application'")
    elif hasattr(app, 'create_app'):
        application = app.create_app()
        debug_log("Found Flask app factory 'app.create_app()'")
    else:
        # Look for any Flask instances
        from flask import Flask
        flask_apps = [getattr(app, attr) for attr in dir(app) 
                     if isinstance(getattr(app, attr, None), Flask)]
        if flask_apps:
            application = flask_apps[0]
            debug_log(f"Found Flask app: {flask_apps[0]}")
        else:
            debug_log("No Flask app found!")
            raise ImportError("No Flask application found in app module")

except Exception as e:
    debug_log(f"Error importing app: {e}")
    debug_log(f"Python path: {sys.path}")
    import traceback
    debug_log(f"Traceback: {traceback.format_exc()}")
    raise

if __name__ == "__main__":
    application.run()