from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, superadmin, organizer, upload, user  # Import all routers
from app.db.base import Base
from app.db.session import engine
from app.models import User, Token
from app.models.tournament import Tournament, Season
from app.models.player import Player, PlayerSeason
from app.models.team import Team, TeamSeason, PlayerPurchase

# This command tells SQLAlchemy to create all database tables based on your models
# It should be run once at startup.
Base.metadata.create_all(bind=engine)

# 1. Create the FastAPI application with enhanced OpenAPI configuration
app = FastAPI(
    title="Cricket Auction Management API",
    version="1.0.0",
    description="""
    ## Cricket Auction Management System

    A comprehensive API for managing cricket tournament auctions with the following features:

    ### 🏏 **Core Features**
    - **User Management**: Authentication, role-based access (Superadmin, Organizer)
    - **Tournament Management**: Create tournaments and seasons
    - **Player Management**: Register players with auto-fill functionality
    - **Team Management**: Register teams with icon players
    - **Auction System**: Multiple auction modes (Random, Manual, Fast Assign)
    - **Budget Management**: Smart budget validation and tracking

    ### 🎯 **Auction Modes**
    1. **Random Mode**: System randomly selects players for bidding
    2. **Manual Mode**: Organizer inputs specific player ID
    3. **Fast Assign Mode**: Direct assignment without bidding process

    ### 💰 **Smart Budget System**
    - Validates team budgets considering future player requirements
    - Calculates maximum bid amounts dynamically
    - Reserves budget for remaining players at base price

    ### 📊 **Team Tracking**
    - Real-time player count and budget tracking
    - Team overview with current status
    - Detailed team rosters with purchase history

    ---
    **Base URL**: `/api`
    """,
    contact={
        "name": "Cricket Auction API Support",
        "email": "support@cricketauction.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Superadmin",
            "description": "Superadmin management endpoints for user approval and system administration"
        },
        {
            "name": "Tournament Management",
            "description": "Create and manage tournaments and seasons"
        },
        {
            "name": "Player Management", 
            "description": "Register players, auto-fill functionality, and player selection for auction"
        },
        {
            "name": "Team Management",
            "description": "Register teams, assign icon players, and configure auction settings"
        },
        {
            "name": "Auction System",
            "description": "Complete auction management with multiple modes and smart budget validation"
        },
        {
            "name": "Team Tracking",
            "description": "Team overview, player rosters, and budget tracking"
        },
        {
            "name": "File Upload",
            "description": "S3 image upload with presigned URLs for player photos and team logos"
        }
    ]
)

# Add CORS middleware to allow all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 2. Include routers
# Public routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# SUPERADMIN routes
app.include_router(superadmin.router, prefix="/api/superadmin", tags=["Superadmin"])

# Organizer routes - organized by functionality
app.include_router(organizer.router, prefix="/api/organizer")

# File upload routes
app.include_router(upload.router, prefix="/api/upload", tags=["File Upload"])

app.include_router(user.router, prefix="/api/user", tags=["User"])

# A simple root endpoint to confirm the API is running.
@app.get("/")
def read_root():
    return {"message": "Welcome to the Cricket Auction API"}