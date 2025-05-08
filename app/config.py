import os
from datetime import timedelta

class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'knust-hesa-default-secret-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for images
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Remember me cookie duration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
        # Add this for cross-device access
    SESSION_COOKIE_SECURE = False  # Set to True in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True  # Keep CSRF protection enabled