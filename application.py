"""
Azure App Service entry point for Django application
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line

# Create WSGI application
application = get_wsgi_application()

# Run startup tasks if this is the main process
if __name__ == '__main__':
    # Collect static files
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Run migrations
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create cache table
    try:
        execute_from_command_line(['manage.py', 'createcachetable'])
    except:
        pass
    
    print("Django application initialized successfully!") 