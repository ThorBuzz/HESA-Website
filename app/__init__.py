from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()
csrf = CSRFProtect()  # Add this line

# Update the create_app function in __init__.py

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # Add this line

    # Add this context processor to inject 'now' into all templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # Import and register blueprints
    from app.routes import main, auth, blog, editor, gallery, foh
    from app.driver_routes import driver  # Import the new driver blueprint
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(blog)
    app.register_blueprint(editor)
    app.register_blueprint(driver)  # Register the driver blueprint
    app.register_blueprint(gallery)
    app.register_blueprint(foh)

    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
    
    return app