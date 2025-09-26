from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.enums.role import Role

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # --- Updated Fields for New Logic ---
    role = Column(Enum(Role), default=Role.USER, nullable=False)
    is_approved = Column(Boolean, default=None, nullable=True)
    auction_limit = Column(Integer, default=0, nullable=False)
    auctions_created = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False)
    
    # --- Relationships ---
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    tournaments = relationship("Tournament", back_populates="organizer", cascade="all, delete-orphan")
    seasons = relationship("Season", back_populates="organizer", cascade="all, delete-orphan")