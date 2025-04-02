"""
Configuration settings for Crypto Trading Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    DEBUG = False
    TESTING = False
    
    # API settings
    SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'true').lower() == 'true'
    
    # Database settings (for future use)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///crypto_bot.db')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Crypto API settings
    COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY')
    
    # Exchange API keys (encrypted in production)
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
    
    KRAKEN_API_KEY = os.environ.get('KRAKEN_API_KEY')
    KRAKEN_API_SECRET = os.environ.get('KRAKEN_API_SECRET')
    
    COINBASE_API_KEY = os.environ.get('COINBASE_API_KEY')
    COINBASE_API_SECRET = os.environ.get('COINBASE_API_SECRET')
    
    # Risk management defaults
    MAX_POSITION_SIZE = float(os.environ.get('MAX_POSITION_SIZE', '10'))
    STOP_LOSS = float(os.environ.get('STOP_LOSS', '5'))
    TAKE_PROFIT = float(os.environ.get('TAKE_PROFIT', '10'))
    MAX_CONCURRENT_TRADES = int(os.environ.get('MAX_CONCURRENT_TRADES', '5'))
    EMERGENCY_STOP_THRESHOLD = float(os.environ.get('EMERGENCY_STOP_THRESHOLD', '15'))
    
    # API key encryption key
    API_KEY_ENCRYPTION_KEY = os.environ.get('API_KEY_ENCRYPTION_KEY')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    # In production, ensure all these are set via environment variables
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    if not os.environ.get('API_KEY_ENCRYPTION_KEY'):
        raise ValueError("API_KEY_ENCRYPTION_KEY environment variable must be set in production")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get config based on environment
def get_config():
    """Get the appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
