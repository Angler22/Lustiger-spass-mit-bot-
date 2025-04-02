"""
User model for the Crypto Trading Bot
Handles user authentication, preferences, and trading settings
"""
import uuid
from datetime import datetime, timedelta
import hashlib
import jwt
from cryptography.fernet import Fernet
import os

class User:
    """User model representing a crypto trading bot user"""
    
    def __init__(self, username, email, password_hash=None, user_id=None):
        """
        Initialize a user object
        
        Args:
            username (str): Username for the user
            email (str): Email address for the user
            password_hash (str, optional): Hashed password. Defaults to None.
            user_id (str, optional): User ID. Defaults to None (generates a new UUID).
        """
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.now()
        self.last_login = None
        self.is_active = True
        
        # Trading preferences
        self.risk_level = "medium"  # low, medium, high
        self.max_position_size = 10.0  # percentage of portfolio
        self.preferred_exchanges = []  # list of exchange IDs
        self.watchlist = []  # list of cryptocurrency symbols
        self.api_keys = {}  # encrypted API keys for exchanges
        self.strategies = []  # enabled trading strategy IDs
        
    def set_password(self, password):
        """
        Set the user's password by hashing it
        
        Args:
            password (str): Plain text password
        """
        # Use SHA-256 for hashing (in production, use a more secure method like bcrypt)
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        """
        Verify if the provided password matches the stored hash
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed == self.password_hash
    
    def add_api_key(self, exchange, api_key, api_secret):
        """
        Add encrypted API keys for an exchange
        
        Args:
            exchange (str): Exchange identifier (e.g., 'binance', 'kraken')
            api_key (str): API key for the exchange
            api_secret (str): API secret for the exchange
        
        Returns:
            bool: Success status
        """
        try:
            # Get encryption key from environment (in production, use a more secure method)
            key = os.environ.get('API_KEY_ENCRYPTION_KEY', 'fallback_dev_key_not_for_production').encode()
            
            # Create cipher for encryption
            cipher = Fernet(key)
            
            # Encrypt API credentials
            encrypted_key = cipher.encrypt(api_key.encode()).decode()
            encrypted_secret = cipher.encrypt(api_secret.encode()).decode()
            
            self.api_keys[exchange] = {
                'key': encrypted_key,
                'secret': encrypted_secret,
                'added_at': datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            print(f"Error adding API key: {e}")
            return False
    
    def get_api_key(self, exchange):
        """
        Get decrypted API keys for an exchange
        
        Args:
            exchange (str): Exchange identifier (e.g., 'binance', 'kraken')
            
        Returns:
            dict: Decrypted API key and secret, or None if not found
        """
        if exchange not in self.api_keys:
            return None
        
        try:
            # Get encryption key from environment
            key = os.environ.get('API_KEY_ENCRYPTION_KEY', 'fallback_dev_key_not_for_production').encode()
            
            # Create cipher for decryption
            cipher = Fernet(key)
            
            # Decrypt API credentials
            encrypted_key = self.api_keys[exchange]['key']
            encrypted_secret = self.api_keys[exchange]['secret']
            
            decrypted_key = cipher.decrypt(encrypted_key.encode()).decode()
            decrypted_secret = cipher.decrypt(encrypted_secret.encode()).decode()
            
            return {
                'key': decrypted_key,
                'secret': decrypted_secret
            }
        except Exception as e:
            print(f"Error decrypting API key: {e}")
            return None
    
    def generate_auth_token(self, expiration=24):
        """
        Generate authentication token for the user
        
        Args:
            expiration (int, optional): Token expiration in hours. Defaults to 24.
            
        Returns:
            str: JWT token
        """
        # Get secret key from environment
        secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
        
        payload = {
            'user_id': self.user_id,
            'username': self.username,
            'exp': datetime.utcnow() + timedelta(hours=expiration)
        }
        
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_auth_token(token):
        """
        Verify an authentication token
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            dict: Token payload if valid, None otherwise
        """
        secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
        
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Invalid token
            return None
    
    def to_dict(self, include_private=False):
        """
        Convert user object to dictionary, optionally excluding private info
        
        Args:
            include_private (bool, optional): Whether to include private info. Defaults to False.
            
        Returns:
            dict: User data as dictionary
        """
        user_dict = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'risk_level': self.risk_level,
            'max_position_size': self.max_position_size,
            'preferred_exchanges': self.preferred_exchanges,
            'watchlist': self.watchlist,
            'strategies': self.strategies
        }
        
        if include_private:
            # Add API keys info (only presence, not the actual keys)
            user_dict['api_keys'] = {k: {'added_at': v['added_at']} for k, v in self.api_keys.items()}
        
        return user_dict
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a user object from dictionary data
        
        Args:
            data (dict): User data dictionary
            
        Returns:
            User: User object
        """
        user = cls(
            username=data['username'],
            email=data['email'],
            password_hash=data.get('password_hash'),
            user_id=data.get('user_id')
        )
        
        # Set additional fields if present
        if 'created_at' in data:
            user.created_at = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and data['last_login']:
            user.last_login = datetime.fromisoformat(data['last_login'])
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'risk_level' in data:
            user.risk_level = data['risk_level']
        if 'max_position_size' in data:
            user.max_position_size = data['max_position_size']
        if 'preferred_exchanges' in data:
            user.preferred_exchanges = data['preferred_exchanges']
        if 'watchlist' in data:
            user.watchlist = data['watchlist']
        if 'api_keys' in data:
            user.api_keys = data['api_keys']
        if 'strategies' in data:
            user.strategies = data['strategies']
        
        return user
