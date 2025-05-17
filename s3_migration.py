# s3_migration.py
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import BlogPost, Event, PersonalityOfTheWeek
from app.utils.s3_helper import upload_file_to_s3
from werkzeug.datastructures import FileStorage

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables (redacted for security)
print(f"AWS_ACCESS_KEY_ID: {'*****' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}")
print(f"AWS_SECRET_ACCESS_KEY: {'*****' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'Not set'}")
print(f"S3_BUCKET: {os.environ.get('S3_BUCKET')}")
print(f"AWS_REGION: {os.environ.get('AWS_REGION')}")
print(f"USE_S3: {os.environ.get('USE_S3')}")

# Set AWS credentials if not already present in environment
# (These would normally be in your .env file)
if not os.environ.get('AWS_ACCESS_KEY_ID'):
    os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key_here'  # Replace with your actual key
if not os.environ.get('AWS_SECRET_ACCESS_KEY'):
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_key_here'  # Replace with your actual key
if not os.environ.get('S3_BUCKET'):
    os.environ['S3_BUCKET'] = 'knust-hesa-images'
if not os.environ.get('AWS_REGION'):
    os.environ['AWS_REGION'] = 'us-east-1'  # or your actual region
if not os.environ.get('USE_S3'):
    os.environ['USE_S3'] = 'True'

app = create_app()

def migrate_images_to_s3():
    with app.app_context():
        print("Starting migration of images to S3...")
        
        # Migrate blog post images
        posts = BlogPost.query.all()
        print(f"Found {len(posts)} blog posts to migrate")
        
        for post in posts:
            if post.image_file and post.image_file != 'default_blog.jpg' and not post.image_file.startswith('http'):
                file_path = os.path.join(app.root_path, 'static', 'blog_pics', post.image_file)
                if os.path.exists(file_path):
                    print(f"Migrating blog post image: {post.image_file}")
                    with open(file_path, 'rb') as file_data:
                        # Convert to FileStorage object which is what upload_file_to_s3 expects
                        file_storage = FileStorage(
                            stream=file_data,
                            filename=os.path.basename(file_path),
                            content_type='image/jpeg'  # Adjust if needed
                        )
                        s3_url = upload_file_to_s3(file_storage, 'blog_pics', acl=None)  # Note: acl=None for S3 buckets with ACLs disabled
                        if s3_url:
                            post.image_file = s3_url
                            print(f"  → Migrated to {s3_url}")
                        else:
                            print(f"  → Failed to migrate {post.image_file}")
                else:
                    print(f"Warning: Image file not found: {file_path}")
        
        # Migrate event images
        events = Event.query.all()
        print(f"Found {len(events)} events to migrate")
        
        for event in events:
            if event.image_file and not event.image_file.startswith('http'):
                file_path = os.path.join(app.root_path, 'static', 'event_pics', event.image_file)
                if os.path.exists(file_path):
                    print(f"Migrating event image: {event.image_file}")
                    with open(file_path, 'rb') as file_data:
                        file_storage = FileStorage(
                            stream=file_data,
                            filename=os.path.basename(file_path),
                            content_type='image/jpeg'  # Adjust if needed
                        )
                        s3_url = upload_file_to_s3(file_storage, 'event_pics', acl=None)
                        if s3_url:
                            event.image_file = s3_url
                            print(f"  → Migrated to {s3_url}")
                        else:
                            print(f"  → Failed to migrate {event.image_file}")
                else:
                    print(f"Warning: Image file not found: {file_path}")
        
        # Migrate POTW images
        potws = PersonalityOfTheWeek.query.all()
        print(f"Found {len(potws)} personalities to migrate")
        
        for potw in potws:
            if potw.image_file and not potw.image_file.startswith('http'):
                file_path = os.path.join(app.root_path, 'static', 'potw_pics', potw.image_file)
                if os.path.exists(file_path):
                    print(f"Migrating POTW image: {potw.image_file}")
                    with open(file_path, 'rb') as file_data:
                        file_storage = FileStorage(
                            stream=file_data,
                            filename=os.path.basename(file_path),
                            content_type='image/jpeg'  # Adjust if needed
                        )
                        s3_url = upload_file_to_s3(file_storage, 'potw_pics', acl=None)
                        if s3_url:
                            potw.image_file = s3_url
                            print(f"  → Migrated to {s3_url}")
                        else:
                            print(f"  → Failed to migrate {potw.image_file}")
                else:
                    print(f"Warning: Image file not found: {file_path}")
        
        # Save all changes to database
        db.session.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate_images_to_s3()