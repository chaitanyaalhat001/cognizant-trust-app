"""
Azure App Service startup script for Django
"""
import os
import sys
import subprocess
from pathlib import Path

def run_startup_tasks():
    """Run Django startup tasks"""
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
        
        # Collect static files
        print("Collecting static files...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Static files collection failed: {result.stderr}")
        else:
            print("Static files collected successfully")
        
        # Run migrations
        print("Running migrations...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
        else:
            print("Migrations completed successfully")
            
        # Create cache table
        print("Creating cache table...")
        subprocess.run([
            sys.executable, 'manage.py', 'createcachetable'
        ], capture_output=True)
        
        print("Startup tasks completed!")
        
    except Exception as e:
        print(f"Startup task error: {e}")

if __name__ == '__main__':
    run_startup_tasks()

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Run startup tasks
run_startup_tasks()

# Create WSGI application
application = get_wsgi_application() 