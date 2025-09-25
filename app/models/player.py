from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.enums.player_type import BattingStyle, BowlingStyle, PlayerRole
from app.enums.auction_status import AuctionStatus

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    village = Column(String(255), nullable=False)
    mobile = Column(String(20), nullable=False, unique=True, index=True)  # Unique mobile number
    photo_url = Column(String(500), nullable=True)
    
    # Player skills - these are the player's general capabilities
    is_wicketkeeper = Column(Boolean, default=False)
    is_batsman = Column(Boolean, default=False)
    is_bowler = Column(Boolean, default=False)
    batting_style = Column(Enum(BattingStyle), nullable=True)
    bowling_style = Column(Enum(BowlingStyle), nullable=True)
    player_role = Column(Enum(PlayerRole), nullable=False)  # Auto-calculated based on skills
    
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    player_seasons = relationship("PlayerSeason", back_populates="player")


class PlayerSeason(Base):
    __tablename__ = "player_seasons"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    
    # Season-specific data
    registered_at = Column(DateTime, default=datetime.now())
    is_selected_for_auction = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)
    
    # Auction status tracking
    auction_status = Column(Enum(AuctionStatus), default=AuctionStatus.PENDING)
    auction_round = Column(Integer, default=1)  # Track which auction round
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (UniqueConstraint('player_id', 'season_id', name='unique_player_season'),)

    # Relationships
    player = relationship("Player", back_populates="player_seasons")
    season = relationship("Season", back_populates="player_seasons")
