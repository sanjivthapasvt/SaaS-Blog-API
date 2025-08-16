import os
import uuid

import aiofiles
from fastapi import HTTPException, UploadFile

BASE_UPLOAD_DIR = "media/uploads"
BASE_MEDIA_URL = "/media/uploads"

os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/gif"}


# async function to save image to disk and return media url
async def save_image(
    image: UploadFile | None, upload_subdir: str | None = None
) -> str | None:
    if not image:
        return None

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, JPEG, PNG, and GIF are allowed.",
        )

    upload_dir = BASE_UPLOAD_DIR
    media_url = BASE_MEDIA_URL

    if upload_subdir:
        upload_dir = os.path.join(BASE_UPLOAD_DIR, upload_subdir)
        media_url = f"{BASE_MEDIA_URL}/{upload_subdir}"
        os.makedirs(upload_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}_{image.filename}"
    file_path = os.path.join(upload_dir, filename)

    # Async write file
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await image.read()
        await out_file.write(content)

    return f"{media_url}/{filename}"
