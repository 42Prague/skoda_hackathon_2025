"""
Configuration settings for the application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    
    # API settings
    API_VERSION = 'v1'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Skill analysis settings
    MIN_SIMILAR_EMPLOYEES = 2  # Minimum employees needed for suggestions
    MAX_SUGGESTIONS_PER_CATEGORY = 5
    
    # Business logic settings
    SKILL_MATCH_THRESHOLD = 0.7  # Similarity threshold for skill matching
    EXPERIENCE_LEVELS = {
        'junior': (0, 2),      # 0-2 years
        'mid': (2, 5),         # 2-5 years  
        'senior': (5, 10),     # 5-10 years
        'expert': (10, 100)    # 10+ years
    }
    
    # Cache settings (for future use)
    CACHE_TIMEOUT = 300  # 5 minutes
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-secret-key'
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
