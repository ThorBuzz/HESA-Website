import boto3
import botocore
from flask import current_app
import os
from werkzeug.utils import secure_filename
from PIL import Image
import io
import uuid

def get_s3_client():
    """Create and return an S3 client using the app config"""
    return boto3.client(
        "s3",
        aws_access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
        region_name=current_app.config.get("AWS_REGION")
    )

# In your s3_helper.py file - update the upload_file_to_s3 function:

def upload_file_to_s3(file, folder='uploads', acl="public-read"):
    """
    Upload a file to S3 with improved quality settings
    :param file: File object to upload
    :param folder: Folder within the bucket to upload to
    :param acl: ACL for the file ('public-read' makes it publicly readable)
    :return: URL of the uploaded file
    """
    try:
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Open and process image with better quality settings
        img = Image.open(file)
        
        # Increase output size for better quality
        output_size = (1200, 900)  # Increased from (800, 600)
        
        # Use LANCZOS resampling for better quality when resizing
        img.thumbnail(output_size, Image.Resampling.LANCZOS)
        
        # Save to in-memory file with high quality
        in_mem_file = io.BytesIO()
        
        # Determine format and save with appropriate quality settings
        original_format = img.format
        if original_format == 'JPEG' or filename.lower().endswith(('.jpg', '.jpeg')):
            img.save(in_mem_file, format='JPEG', quality=95, optimize=True)
            content_type = 'image/jpeg'
        elif original_format == 'PNG' or filename.lower().endswith('.png'):
            img.save(in_mem_file, format='PNG', optimize=True)
            content_type = 'image/png'
        else:
            # Default to JPEG with high quality
            img.save(in_mem_file, format='JPEG', quality=95, optimize=True)
            content_type = 'image/jpeg'
        
        in_mem_file.seek(0)
        
        # Full path in S3
        s3_path = f"{folder}/{unique_filename}"
        
        # Extra args for upload with proper content type
        extra_args = {
            "ContentType": content_type
        }
        
        # Only add ACL if it's not None
        if acl is not None:
            extra_args["ACL"] = acl
        
        # Upload to S3
        s3_client = get_s3_client()
        s3_client.upload_fileobj(
            in_mem_file,
            current_app.config.get("S3_BUCKET"),
            s3_path,
            ExtraArgs=extra_args
        )
        
        # Generate URL
        file_url = f"{current_app.config.get('S3_LOCATION')}{s3_path}"
        return file_url
        
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        return None
    
def delete_file_from_s3(file_url):
    """
    Delete a file from S3 using its URL
    :param file_url: Full URL of the file to delete
    :return: True if successful, False otherwise
    """
    try:
        # Extract key from URL
        bucket = current_app.config.get("S3_BUCKET")
        s3_location = current_app.config.get("S3_LOCATION")
        
        if file_url.startswith(s3_location):
            key = file_url[len(s3_location):]
            
            # Delete the file
            s3_client = get_s3_client()
            s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        return False
    except Exception as e:
        print(f"S3 delete error: {str(e)}")
        return False