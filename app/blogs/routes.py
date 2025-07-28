from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Form
from users.models import User
from core.database import get_session
from sqlmodel import Session, select
from blogs.models import Blog
from blogs.schema import CommentsData, BlogRead
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException
import os
import shutil
import uuid

router = APIRouter()

MEDIA_URL = "/media/uploads/blogs" 
UPLOAD_DIR = "media/uploads/blogs"

os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/gif"} #for validation of thumbnail

@router.post("/create")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    thumbnail: UploadFile | None = File(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
        Post method for blog to create new blog needs to be authenticated to perform this action.
        Require multipart/formdata input
    """
    try:
        thumbnail_url = None
        
        #save thumbnail if it is uploaded 
        if thumbnail:
            if thumbnail.content_type not in ALLOWED_IMAGE_TYPES: #check if the file is image or not
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only Jpg, Jpeg, Png and Gif are allowed"
                )
            # generate a unique filename to avoid conflicts
            filename = f"{uuid.uuid4().hex}_{thumbnail.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            #save file to disk
            with open (file_path, 'wb') as bufffer:
                shutil.copyfileobj(thumbnail.file, bufffer)
            
            thumbnail_url = f"{MEDIA_URL}/{filename}"

        new_blog = Blog(
            title=title,
            content=content,
            thumbnail_url=thumbnail_url, 
            uploaded_by=current_user.id
            )     
        
        session.add(new_blog)
        session.commit()
        session.refresh(new_blog)
        title = new_blog.title
        
        return {"title": title, "detail": "Successfully created the blog"}

    
    except Exception as e:
        raise (HTTPException(status_code=500, detail=f"Something went wrong {str(e)}"))
    
@router.get("/all", response_model=List[BlogRead])
async def get_all_blog(session: Session = Depends(get_session)):
    blogs = session.exec(select(Blog)).all()
    return blogs

@router.get("/mine", response_model=List[BlogRead])
async def get_current_user_blog(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    blogs = session.exec(select(Blog).where(Blog.uploaded_by == current_user.id)).all()
    return blogs