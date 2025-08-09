#!/usr/bin/env python3
"""
Debug startup script for Azure Django deployment
This script provides verbose output to help diagnose startup issues
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def print_environment():
    """Print environment information"""
    logger.info("=== ENVIRONMENT INFO ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Print important environment variables
    env_vars = [
        'DJANGO_SETTINGS_MODULE',
        'PYTHONPATH',
        'WEBSITE_HOSTNAME',
        'HTTP_PLATFORM_PORT',
        'DEBUG'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        logger.info(f"{var}: {value}")

def check_files():
    """Check if important files exist"""
    logger.info("=== FILE CHECK ===")
    
    files_to_check = [
        'manage.py',
        'cognizanttrust/settings.py',
        'cognizanttrust/wsgi.py',
        'requirements.txt',
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path} exists")
        else:
            logger.error(f"❌ {file_path} NOT FOUND")

def test_django_import():
    """Test if Django can be imported and configured"""
    logger.info("=== DJANGO IMPORT TEST ===")
    
    try:
        import django
        logger.info(f"✅ Django version: {django.get_version()}")
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
        django.setup()
        logger.info("✅ Django setup successful")
        
        # Test WSGI app
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
        logger.info("✅ WSGI application created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Django setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def collect_static_files():
    """Collect static files"""
    logger.info("=== COLLECTING STATIC FILES ===")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput', '--verbosity=2'
        ], capture_output=True, text=True, timeout=120)
        
        logger.info(f"Static collection stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Static collection stderr: {result.stderr}")
            
        if result.returncode == 0:
            logger.info("✅ Static files collected successfully")
        else:
            logger.error(f"❌ Static collection failed with code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Static collection timed out")
    except Exception as e:
        logger.error(f"❌ Static collection error: {e}")

def run_migrations():
    """Run database migrations"""
    logger.info("=== RUNNING MIGRATIONS ===")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate', '--verbosity=2'
        ], capture_output=True, text=True, timeout=120)
        
        logger.info(f"Migration stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Migration stderr: {result.stderr}")
            
        if result.returncode == 0:
            logger.info("✅ Migrations completed successfully")
        else:
            logger.error(f"❌ Migrations failed with code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Migrations timed out")
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")

def start_gunicorn():
    """Start gunicorn server"""
    logger.info("=== STARTING GUNICORN ===")
    
    port = os.environ.get('HTTP_PLATFORM_PORT', '8000')
    
    gunicorn_cmd = [
        sys.executable, '-m', 'gunicorn',
        'cognizanttrust.wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--timeout', '600',
        '--log-level', 'info',
        '--access-logfile', '-',
        '--error-logfile', '-'
    ]
    
    logger.info(f"Running: {' '.join(gunicorn_cmd)}")
    
    # Start gunicorn and don't return (exec replacement)
    os.execv(sys.executable, gunicorn_cmd)

def main():
    """Main startup function"""
    logger.info("🚀 STARTING AZURE DJANGO DEPLOYMENT DEBUG")
    
    print_environment()
    check_files()
    
    django_ok = test_django_import()
    if not django_ok:
        logger.error("Django setup failed - cannot continue")
        sys.exit(1)
    
    collect_static_files()
    run_migrations()
    
    logger.info("✅ DEBUG STARTUP COMPLETED - Starting WSGI server")
    start_gunicorn()

if __name__ == '__main__':
    main() 