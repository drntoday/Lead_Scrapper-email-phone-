import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///leads.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Rate limiting settings
    REQUEST_DELAY_MIN = 3.0
    REQUEST_DELAY_MAX = 7.0
    
    # Default user agent
    USER_AGENT = 'LeadGenBot/1.0 (Ethical Data Aggregation)'
    
    # Upload folder for exports
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    
    # Allowed export formats
    EXPORT_FORMATS = ['csv', 'xlsx', 'json']

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
