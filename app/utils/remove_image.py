import asyncio
import os

from fastapi import HTTPException


async def remove_image(image_url: str):
    # Remove leading slash if present
    image_path = image_url.lstrip("/")

    # Check if file exists
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, os.remove, image_path)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied to delete image")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete image")
