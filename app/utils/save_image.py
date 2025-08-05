import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

BASE_UPLOAD_DIR = "media/uploads"
BASE_MEDIA_URL = "/media/uploads"

os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/gif"}

def save_image(image: UploadFile | None, upload_subdir: str | None = None) -> str | None:
    """
    Validates and saves an uploaded image.
    Returns the relative media URL of the saved file.
    """
    if not image:
        return None

    # Validate image type
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, JPEG, PNG, and GIF are allowed."
        )

    # Define subdirectory if provided
    upload_dir = BASE_UPLOAD_DIR
    media_url = BASE_MEDIA_URL
    
    if upload_subdir:
        upload_dir = os.path.join(BASE_UPLOAD_DIR, upload_subdir)
        media_url = f"{BASE_MEDIA_URL}/{upload_subdir}"
        os.makedirs(upload_dir, exist_ok=True)

    # Generate a unique filename
    filename = f"{uuid.uuid4().hex}_{image.filename}"
    file_path = os.path.join(upload_dir, filename)

    # Save image to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return f"{media_url}/{filename}"
