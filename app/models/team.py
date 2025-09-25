from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    logo_url = Column(String(500), nullable=True)
    owner_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    team_seasons = relationship("TeamSeason", back_populates="team")


class TeamSeason(Base):
    __tablename__ = "team_seasons"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    icon_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)  # Icon player (pre-assigned)
    
    # Auction budget and constraints
    total_budget = Column(Numeric(15, 2), nullable=False)  # Total budget for this team in this season
    remaining_budget = Column(Numeric(15, 2), nullable=False)  # Remaining budget after purchases
    max_players = Column(Integer, nullable=False)  # Maximum players allowed in team
    current_players = Column(Integer, default=0)  # Current number of players in team
    
    created_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    
    # Unique constraint to prevent duplicate team registrations in same season
    __table_args__ = (UniqueConstraint('team_id', 'season_id', name='unique_team_season'),)

    # Relationships
    team = relationship("Team", back_populates="team_seasons")
    season = relationship("Season", back_populates="team_seasons")
    icon_player = relationship("Player", foreign_keys=[icon_player_id])
    player_purchases = relationship("PlayerPurchase", back_populates="team_season")


class PlayerPurchase(Base):
    __tablename__ = "player_purchases"

    id = Column(Integer, primary_key=True, index=True)
    team_season_id = Column(Integer, ForeignKey("team_seasons.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    purchase_price = Column(Numeric(15, 2), nullable=False)  # Price paid for the player
    is_icon_player = Column(Boolean, default=False)  # True if this is the icon player (free)
    purchased_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    
    # Unique constraint to prevent same player being bought by multiple teams in same season
    __table_args__ = (UniqueConstraint('team_season_id', 'player_id', name='unique_player_purchase'),)

    # Relationships
    team_season = relationship("TeamSeason", back_populates="player_purchases")
    player = relationship("Player")
