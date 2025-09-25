"""
S3 helper utilities for Cricket Auction API.

Handles S3 operations including presigned URL generation and file management.
"""

import boto3
import uuid
from datetime import datetime, timedelta
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.core.config import settings


class S3Helper:
    """Helper class for S3 operations."""
    
    def __init__(self):
        """Initialize S3 client with AWS credentials."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def generate_presigned_upload_url(self, file_type: str = "image", 
                                    content_type: str = "image/jpeg",
                                    expiration: int = 3600) -> dict:
        """
        Generate a presigned URL for uploading files to S3.
        
        Args:
            file_type: Type of file (image, document, etc.)
            content_type: MIME type of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            dict: Contains upload_url and file_key
        """
        try:
            # Generate unique file key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = self._get_file_extension(content_type)
            
            file_key = f"{file_type}s/{timestamp}_{unique_id}{file_extension}"
            
            # Generate presigned URL for PUT operation
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            
            # Generate the final URL that will be stored in database
            file_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            
            return {
                "upload_url": presigned_url,
                "file_key": file_key,
                "file_url": file_url,
                "expires_in": expiration
            }
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
    
    def generate_presigned_download_url(self, file_key: str, 
                                      expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading/viewing files from S3.
        
        Args:
            file_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned download URL
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )
            return presigned_url
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            file_key: S3 object key to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
            
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    def extract_file_key_from_url(self, file_url: str) -> Optional[str]:
        """
        Extract S3 file key from full URL.
        
        Args:
            file_url: Full S3 URL
            
        Returns:
            str: File key or None if invalid URL
        """
        if not file_url:
            return None
            
        try:
            # Handle different S3 URL formats
            if f"{self.bucket_name}.s3." in file_url:
                # Format: https://bucket.s3.region.amazonaws.com/key
                return file_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
            elif f"s3.{settings.AWS_REGION}.amazonaws.com/{self.bucket_name}/" in file_url:
                # Format: https://s3.region.amazonaws.com/bucket/key
                return file_url.split(f"s3.{settings.AWS_REGION}.amazonaws.com/{self.bucket_name}/")[1]
            else:
                return None
                
        except (IndexError, AttributeError):
            return None
    
    def _get_file_extension(self, content_type: str) -> str:
        """Get file extension from content type."""
        extensions = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        return extensions.get(content_type, '.jpg')


# Global instance
s3_helper = S3Helper()
