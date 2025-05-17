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

def upload_file_to_s3(file, folder='uploads', acl="public-read"):
    """
    Upload a file to S3
    :param file: File object to upload
    :param folder: Folder within the bucket to upload to
    :param acl: ACL for the file ('public-read' makes it publicly readable)
    :return: URL of the uploaded file
    """
    try:
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Resize image before uploading
        img = Image.open(file)
        output_size = (800, 600)
        img.thumbnail(output_size)
        
        # Save to in-memory file
        in_mem_file = io.BytesIO()
        img.save(in_mem_file, format=img.format if img.format else 'JPEG')
        in_mem_file.seek(0)
        
        # Full path in S3
        s3_path = f"{folder}/{unique_filename}"
        
        # Extra args for upload
        extra_args = {
            "ContentType": file.content_type
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