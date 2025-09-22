from fastapi import FastAPI
from app.api.endpoints import auth  # Imports the router from your auth endpoint file
from app.db.base import Base
from app.db.session import engine
from app.models.user import User  # Import User model
from app.models.token import Token  # Import Token model

# This command tells SQLAlchemy to create all database tables based on your models
# It should be run once at startup.
Base.metadata.create_all(bind=engine)

# 1. This creates the main FastAPI application object.
app = FastAPI(title="Cricket Auction API")

# 2. This connects your authentication endpoints (like /signup) to the main app.
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# A simple root endpoint to confirm the API is running.
@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket Auction API"}