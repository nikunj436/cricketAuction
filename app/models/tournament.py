from unicodedata import category
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.enums import TournamentCategory, AuctionMode

class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    logo_key = Column(String(500), nullable=True)
    category = Column(Enum(TournamentCategory), nullable=False, default=TournamentCategory.OTHER)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    organizer = relationship("User", back_populates="tournaments")
    seasons = relationship("Season", back_populates="tournament", cascade="all, delete-orphan")

class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    registration_open = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Auction Configuration
    base_price = Column(Numeric(15, 2), nullable=True)  # Base price for all players (e.g., 1 lakh)
    max_players_per_team = Column(Integer, nullable=True)  # Max players each team can have
    total_budget_per_team = Column(Numeric(15, 2), nullable=True)  # Total budget for each team
    auction_configured = Column(Boolean, default=False)  # Whether auction settings are configured
    auction_started = Column(Boolean, default=False)  # Whether auction has started
    auction_mode = Column(Enum(AuctionMode), default=AuctionMode.RANDOM)  # Auction mode
    current_auction_round = Column(Integer, default=1)  # Current auction round

    # Relationships
    tournament = relationship("Tournament", back_populates="seasons")
    organizer = relationship("User", back_populates="seasons")
    player_seasons = relationship("PlayerSeason", back_populates="season", cascade="all, delete-orphan")
    team_seasons = relationship("TeamSeason", back_populates="season", cascade="all, delete-orphan")
