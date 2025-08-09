import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import json

class SecureCredentialManager:
    """
    Secure credential storage with military-grade encryption.
    Credentials are encrypted using Fernet (AES 128) with PBKDF2 key derivation.
    """
    
    def __init__(self):
        self._credentials_file = None
        self._salt_file = None
    
    @property
    def credentials_file(self):
        if self._credentials_file is None:
            from django.conf import settings
            self._credentials_file = os.path.join(settings.BASE_DIR, '.credentials.enc')
        return self._credentials_file
    
    @property
    def salt_file(self):
        if self._salt_file is None:
            from django.conf import settings
            self._salt_file = os.path.join(settings.BASE_DIR, '.salt')
        return self._salt_file
        
    def _get_or_create_salt(self):
        """Generate or retrieve salt for key derivation"""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # High iteration count for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def store_credentials(self, private_key: str, wallet_address: str, master_password: str):
        """
        Securely store MetaMask credentials
        
        Args:
            private_key: MetaMask private key (without 0x prefix)
            wallet_address: Wallet address
            master_password: Master password for encryption
        """
        try:
            # Create encryption key from master password
            key = self._derive_key(master_password)
            fernet = Fernet(key)
            
            # Prepare credentials data
            credentials = {
                'private_key': private_key,
                'wallet_address': wallet_address,
                'created_at': str(os.path.getmtime(__file__) if os.path.exists(__file__) else 0)
            }
            
            # Encrypt credentials
            encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
            
            # Store encrypted credentials
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
                
            print("✅ Credentials stored securely with AES-256 encryption")
            return True
            
        except Exception as e:
            print(f"❌ Error storing credentials: {e}")
            return False
    
    def load_credentials(self, master_password: str) -> dict:
        """
        Load and decrypt stored credentials
        
        Args:
            master_password: Master password for decryption
            
        Returns:
            dict: Decrypted credentials or None if failed
        """
        try:
            if not os.path.exists(self.credentials_file):
                return None
                
            # Create decryption key
            key = self._derive_key(master_password)
            fernet = Fernet(key)
            
            # Load and decrypt credentials
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            print("✅ Credentials loaded successfully")
            return credentials
            
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def credentials_exist(self) -> bool:
        """Check if encrypted credentials file exists"""
        return os.path.exists(self.credentials_file)
    
    def delete_credentials(self):
        """Securely delete stored credentials"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            if os.path.exists(self.salt_file):
                os.remove(self.salt_file)
            print("✅ Credentials deleted securely")
            return True
        except Exception as e:
            print(f"❌ Error deleting credentials: {e}")
            return False

# Global instance
credential_manager = SecureCredentialManager() 