#!/usr/bin/env python
"""
Simple health check for Django app in Azure
"""
import os
import sys
import django
from django.conf import settings

def health_check():
    print("=== Django Health Check ===")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cognizanttrust.settings')
    
    try:
        # Test Django setup
        django.setup()
        print("✅ Django setup successful")
        
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        
        # Test static files configuration
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"✅ STATIC_URL: {settings.STATIC_URL}")
        
        # Test allowed hosts
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        
        print("=== Health Check PASSED ===")
        return True
        
    except Exception as e:
        print(f"❌ Health Check FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    health_check() 