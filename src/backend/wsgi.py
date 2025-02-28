# standard library
import os  # Access environment variables

# Internal imports
from .app import create_application  # Import the application factory function

# Configure logger
# from core.utils.logger import get_logger
# logger = get_logger(__name__)

# Determine environment from parameter or FLASK_ENV environment variable
env = os.environ.get('FLASK_ENV', 'development')

# Create the Flask application instance using the factory function
application = create_application(env)

# Export the application instance for WSGI servers like Gunicorn
if __name__ == "__main__":
    application = create_application('development')
    application.run(debug=True)