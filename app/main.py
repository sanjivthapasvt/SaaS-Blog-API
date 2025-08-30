from dotenv import load_dotenv

from app.core.app_factory import create_app

# Load environment variables
load_dotenv()

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
