from fastapi import APIRouter, Depends
from auth.models import User
from core.database import get_session
from sqlmodel import Session
from blogs.models import Blog
from blogs.schema import BlogCreate, CommentsData, BlogCreated
from auth.auth import get_current_user
from fastapi.exceptions import HTTPException

router = APIRouter()


@router.post("/create")
def create_blog_post(blog_data: BlogCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        new_blog = Blog(title=blog_data.title, content=blog_data.content, uploaded_by=current_user.id)     
        session.add(new_blog)
        session.commit()
        session.refresh(new_blog)
        title = new_blog.title
        
        return {"title": title, "detail": "Successfully created the blog"}

    
    except Exception as e:
        raise (HTTPException(status_code=400, detail=f"Something went wrong {str(e)}"))