import os
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class ProductionSecurityManager:
    """
    Production-grade security manager for blockchain credentials.
    Implements multiple security layers for real production use.
    """
    
    def __init__(self):
        self.max_failed_attempts = 3
        self.lockout_duration = 1800  # 30 minutes
        self.session_timeout = 3600   # 1 hour
        self.key_rotation_days = 90   # Rotate encryption key every 90 days
        
    def validate_master_password(self, password: str) -> dict:
        """
        Validate master password with enterprise-grade security
        
        Args:
            password: Master password to validate
            
        Returns:
            dict: Validation result with security metrics
        """
        validation = {
            'valid': False,
            'score': 0,
            'requirements': [],
            'warnings': []
        }
        
        # Length requirement (minimum 16 characters for production)
        if len(password) >= 16:
            validation['score'] += 25
            validation['requirements'].append('✅ Length: 16+ characters')
        else:
            validation['requirements'].append('❌ Length: Need 16+ characters')
            validation['warnings'].append('Password too short for production use')
        
        # Complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if has_upper:
            validation['score'] += 15
            validation['requirements'].append('✅ Uppercase letters')
        else:
            validation['requirements'].append('❌ Need uppercase letters')
        
        if has_lower:
            validation['score'] += 15
            validation['requirements'].append('✅ Lowercase letters')
        else:
            validation['requirements'].append('❌ Need lowercase letters')
        
        if has_digit:
            validation['score'] += 15
            validation['requirements'].append('✅ Numbers')
        else:
            validation['requirements'].append('❌ Need numbers')
        
        if has_special:
            validation['score'] += 15
            validation['requirements'].append('✅ Special characters')
        else:
            validation['requirements'].append('❌ Need special characters')
        
        # No common patterns
        common_patterns = ['123456', 'password', 'admin', 'qwerty', 'cognizant']
        if not any(pattern in password.lower() for pattern in common_patterns):
            validation['score'] += 15
            validation['requirements'].append('✅ No common patterns')
        else:
            validation['requirements'].append('❌ Contains common patterns')
            validation['warnings'].append('Avoid common words/patterns')
        
        # Final validation
        validation['valid'] = validation['score'] >= 85
        
        if validation['valid']:
            validation['strength'] = 'PRODUCTION READY'
        elif validation['score'] >= 70:
            validation['strength'] = 'GOOD (but enhance for production)'
        else:
            validation['strength'] = 'WEAK (not suitable for production)'
        
        return validation
    
    def check_access_attempt(self, ip_address: str, user_id: str = 'admin') -> bool:
        """
        Check if access attempt is allowed (rate limiting)
        
        Args:
            ip_address: Client IP address
            user_id: User identifier
            
        Returns:
            bool: True if access allowed
        """
        key = f"failed_attempts_{ip_address}_{user_id}"
        attempts = cache.get(key, 0)
        
        if attempts >= self.max_failed_attempts:
            logger.warning(f"🚨 Access blocked for {ip_address} - too many failed attempts")
            return False
        
        return True
    
    def record_failed_attempt(self, ip_address: str, user_id: str = 'admin'):
        """Record failed access attempt"""
        key = f"failed_attempts_{ip_address}_{user_id}"
        attempts = cache.get(key, 0) + 1
        cache.set(key, attempts, self.lockout_duration)
        
        logger.warning(f"⚠️ Failed attempt #{attempts} from {ip_address}")
        
        if attempts >= self.max_failed_attempts:
            logger.critical(f"🚨 IP {ip_address} LOCKED OUT - {attempts} failed attempts")
    
    def clear_failed_attempts(self, ip_address: str, user_id: str = 'admin'):
        """Clear failed attempts after successful access"""
        key = f"failed_attempts_{ip_address}_{user_id}"
        cache.delete(key)
    
    def create_session_token(self, user_id: str) -> str:
        """Create secure session token for auto-mode"""
        timestamp = int(time.time())
        random_data = secrets.token_urlsafe(32)
        
        # Create session token with timestamp and random data
        token_data = f"{user_id}:{timestamp}:{random_data}"
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Store session in cache
        session_key = f"auto_session_{token_hash}"
        cache.set(session_key, {
            'user_id': user_id,
            'created_at': timestamp,
            'ip_address': None,  # To be set when used
            'last_activity': timestamp
        }, self.session_timeout)
        
        return token_hash
    
    def validate_session_token(self, token: str, ip_address: str = None) -> bool:
        """Validate session token for auto-mode"""
        session_key = f"auto_session_{token}"
        session_data = cache.get(session_key)
        
        if not session_data:
            logger.warning("🚨 Invalid or expired session token")
            return False
        
        # Update last activity
        session_data['last_activity'] = int(time.time())
        if ip_address:
            session_data['ip_address'] = ip_address
        
        cache.set(session_key, session_data, self.session_timeout)
        return True
    
    def get_security_headers(self) -> dict:
        """Get security headers for production"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data:;",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def audit_log(self, action: str, user_id: str, ip_address: str, details: dict = None):
        """Create audit log entry for security monitoring"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {},
            'level': 'INFO'
        }
        
        # Log to Django logger
        logger.info(f"AUDIT: {action} by {user_id} from {ip_address}")
        
        # In production, you might want to send this to a SIEM system
        # or store in a separate audit database
    
    def check_wallet_security(self, wallet_address: str) -> dict:
        """Check wallet security status"""
        # This could integrate with blockchain security services
        # For now, basic checks
        
        security_check = {
            'address_valid': len(wallet_address) == 42 and wallet_address.startswith('0x'),
            'risk_level': 'LOW',  # Would be determined by external security service
            'warnings': [],
            'recommendations': []
        }
        
        if not security_check['address_valid']:
            security_check['warnings'].append('Invalid wallet address format')
            security_check['risk_level'] = 'HIGH'
        
        # Add more checks based on your security requirements
        security_check['recommendations'].append('Regular security audits recommended')
        security_check['recommendations'].append('Monitor wallet for unusual activity')
        
        return security_check

# Global security manager instance
security_manager = ProductionSecurityManager() 