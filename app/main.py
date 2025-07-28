from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi import FastAPI
from core.database import create_db_and_tables
from auth.routes import router as auth_router
from blogs.routes import router as blog_router
from fastapi.staticfiles import StaticFiles
from users.routes import router as users_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


app.mount("/media", StaticFiles(directory="media"), name="media")
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(blog_router, prefix="/blog", tags=["Blog"])
app.include_router(users_router, prefix="/user", tags=["Users"])

@app.get("/")
def home():
    return {"message": "Welcome to SaaS-blog-API"}
