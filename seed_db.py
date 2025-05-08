from app import create_app, db
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
                'username': 'ThorLazerman',
                'email': 'Pwavrahenry06@gmail.com',
                'password': 'bigbadbucky',
                'role': 'admin'
            },
            {
                'username': 'Godwin',
                'email': 'mawulikplimgodwin@gmail.com',
                'password': 'gymn748512693hesa',
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

# Update the main function to include driver seeding
if __name__ == '__main__':
    seed_users()
    seed_drivers()
