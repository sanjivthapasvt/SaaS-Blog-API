import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "media/uploads/blogs"
MEDIA_URL = "/media/uploads/blogs" 

os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/gif"} #for validation of thumbnail

def save_thumbnail(thumbnail: UploadFile | None) -> str | None:
    """
    Validates and saves an uploaded image thumbnail.
    """
    if not thumbnail:
        return None

    if thumbnail.content_type not in ALLOWED_IMAGE_TYPES: #check if the file is image or not
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, JPEG, PNG, and GIF are allowed."
        )

    # generate a unique filename to avoid conflicts
    filename = f"{uuid.uuid4().hex}_{thumbnail.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    #save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(thumbnail.file, buffer)

    return f"{MEDIA_URL}/{filename}"