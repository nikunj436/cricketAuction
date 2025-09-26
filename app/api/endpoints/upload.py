"""
Upload endpoints for Cricket Auction API.

Handles file upload operations using S3 presigned URLs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api import deps
from app.models import User
from app.utils.s3_helper import s3_helper
from app.enums import UploadType

router = APIRouter()

@router.post("/presigned-url", tags=["File Upload"])
def generate_upload_url(
    upload_type: str = Query("player_photo", description="Type of upload: player_photo or team_logo"),
    content_type: str = Query("image/jpeg", description="MIME type of the image file"),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate a presigned URL for uploading image files to S3.
    
    Upload types:
    - player_photo
    - team_logo
    - tournament_logo
    
    Supported image types:
    - image/jpeg, image/jpg, image/png, image/gif, image/webp
    """
    # Validate content type - only images allowed
    allowed_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
    ]
    
    # Validate upload type
    allowed_upload_types = ["player_photo", "team_logo","tournament_logo"]
    if upload_type not in allowed_upload_types:
        raise HTTPException(
            status_code=400,
            detail=f"Upload type '{upload_type}' not allowed. Supported types: {', '.join(allowed_upload_types)}"
        )
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Content type '{content_type}' not allowed. Supported types: {', '.join(allowed_types)}"
        )
    
    # Map upload type to S3 folder
    folder_mapping = {
        "player_photo": UploadType.PLAYER_PHOTO.value,
        "team_logo": UploadType.TEAM_LOGO.value,
        "tournament_logo": UploadType.TOURNAMENT_LOGO.value,
    }
    
    # Generate presigned URL for image upload
    result = s3_helper.generate_presigned_upload_url(
        file_type=folder_mapping[upload_type],
        content_type=content_type,
        expiration=3600  # 1 hour
    )
    
    return {
        "upload_url": result["upload_url"],
        "file_url": result["file_url"],
        "file_key": result["file_key"],
        "expires_in": result["expires_in"],
        "instructions": {
            "method": "PUT",
            "headers": {
                "Content-Type": content_type
            },
            "note": f"Upload your {upload_type.replace('_', ' ')} to the upload_url using PUT method. After successful upload, use file_url in your player/team registration API calls."
        }
    }   

@router.get("/download-url", tags=["File Upload"])
def generate_download_url(
    file_url: str = Query(..., description="S3 file URL to generate download link for"),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate a presigned URL for downloading/viewing files from S3.
    """
    # Extract file key from URL
    file_key = s3_helper.extract_file_key_from_url(file_url)
    
    if not file_key:
        raise HTTPException(
            status_code=400,
            detail="Invalid S3 file URL provided"
        )
    
    # Generate presigned download URL
    download_url = s3_helper.generate_presigned_download_url(
        file_key=file_key,
        expiration=3600  # 1 hour
    )
    
    return {
        "download_url": download_url,
        "expires_in": 3600,
        "original_url": file_url
    }

@router.delete("/file", tags=["File Upload"])
def delete_file(
    file_url: str = Query(..., description="S3 file URL to delete"),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a file from S3 storage.
    """
    # Extract file key from URL
    file_key = s3_helper.extract_file_key_from_url(file_url)
    
    if not file_key:
        raise HTTPException(
            status_code=400,
            detail="Invalid S3 file URL provided"
        )
    
    # Delete file
    success = s3_helper.delete_file(file_key)
    
    if success:
        return {
            "message": "File deleted successfully",
            "deleted_url": file_url
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file"
        )
