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
from app.models import User

def seed_users():
    app = create_app()
    with app.app_context():
        # Check if users already exist
        if User.query.count() > 0:
            print("Database already has users. Skipping...")
            return
        
        # Create users
        users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin',
                'role': 'admin'
            },
            {
                'username': 'editor',
                'email': 'editor@example.com',
                'password': 'editorpassword',
                'role': 'editor'
            },
            {
                'username': 'student',
                'email': 'student@example.com',
                'password': 'studentpassword',
                'role': 'student'
            }
        ]
        
        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        db.session.commit()
        print("Database seeded successfully with users!")

# Add this to seed_db.py

def seed_drivers():
    app = create_app()
    with app.app_context():
        # Check if drivers already exist
        drivers_count = User.query.filter_by(role='driver').count()
        if drivers_count > 0:
            print("Drivers already exist. Skipping...")
            return
        
        # Create driver users
        drivers = [
            {
                'username': 'driver1',
                'email': 'driver1@example.com',
                'password': 'driverpass1',
                'role': 'driver'
            },
            {
                'username': 'driver2',
                'email': 'driver2@example.com',
                'password': 'driverpass2',
                'role': 'driver'
            },
            {
                'username': 'driver3',
                'email': 'driver3@example.com',
                'password': 'driverpass3',
                'role': 'driver'
            }
        ]
        
        for driver_data in drivers:
            driver = User(
                username=driver_data['username'],
                email=driver_data['email'],
                role=driver_data['role']
            )
            driver.set_password(driver_data['password'])
            db.session.add(driver)
        
        db.session.commit()
        print("Database seeded successfully with drivers!")

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
    from app.routes import main, auth, blog, editor
    from app.driver_routes import driver  # Import the new driver blueprint
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(blog)
    app.register_blueprint(editor)
    app.register_blueprint(driver)  # Register the driver blueprint
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app