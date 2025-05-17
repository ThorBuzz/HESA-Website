import os
from datetime import timedelta
from dotenv import load_dotenv

class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'knust-hesa-default-secret-key'
    
    # Database configuration
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    
    # Local offline testing.
    # SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'site.db')}"

    # Local but affect postgres.
    # SQLALCHEMY_DATABASE_URI = 'postgresql://fallingstarcampusmarket_owner:4LQ6xdtFAlNS@ep-morning-star-a8n2df7n.eastus2.azure.neon.tech/fallingstarcampusmarket?sslmode=require'

    # external render
    SQLALCHEMY_DATABASE_URI = 'postgresql://hesa_website_database_user:VKp5X370nKMVPIQMiLhaagCH3JA3KPDY@dpg-d0ehvu95pdvs73anp8hg-a.oregon-postgres.render.com/hesa_website_database'

    # internal render
    # SQLALCHEMY_DATABASE_URI = 'postgresql://hesa_website_database_user:VKp5X370nKMVPIQMiLhaagCH3JA3KPDY@dpg-d0ehvu95pdvs73anp8hg-a/hesa_website_database'


    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for local development (fallback)
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # S3 configuration
    S3_BUCKET = os.environ.get('S3_BUCKET', 'knust-hesa-images')
    S3_LOCATION = f'https://{S3_BUCKET}.s3.amazonaws.com/'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'eu-north-1')  # Change this to your chosen region
    
    # Use S3 for file uploads (set to False for local development)
    USE_S3 = os.environ.get('USE_S3', 'True').lower() == 'true'
    
    # Remember me cookie duration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    # Add this for cross-device access
    SESSION_COOKIE_SECURE = False  # Set to True in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True  # Keep CSRF protection enabled