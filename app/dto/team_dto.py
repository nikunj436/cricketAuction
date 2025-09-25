from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Team DTOs
class TeamCreate(BaseModel):
    name: str
    owner_name: str
    logo_url: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Team name must be at least 2 characters')
        return v.strip()

    @field_validator('owner_name')
    @classmethod
    def validate_owner_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Owner name must be at least 2 characters')
        return v.strip()

class Team(BaseModel):
    id: int
    name: str
    owner_name: str
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Team Season DTOs
class TeamSeasonCreate(BaseModel):
    team_id: int
    icon_player_id: Optional[int] = None  # Icon player (pre-assigned to team)

class TeamSeason(BaseModel):
    id: int
    team_id: int
    season_id: int
    icon_player_id: Optional[int] = None
    current_players: int
    max_players: int
    remaining_budget: float
    total_budget: float
    created_at: datetime
    updated_at: datetime
    is_active: bool
    team: Team

    class Config:
        from_attributes = True

# Auction Configuration DTOs
class AuctionConfigCreate(BaseModel):
    base_price: float
    max_players_per_team: int
    total_budget_per_team: float

    @field_validator('base_price')
    @classmethod
    def validate_base_price(cls, v):
        if v <= 0:
            raise ValueError('Base price must be greater than 0')
        return v

    @field_validator('max_players_per_team')
    @classmethod
    def validate_max_players(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Max players per team must be between 1 and 50')
        return v

    @field_validator('total_budget_per_team')
    @classmethod
    def validate_total_budget(cls, v):
        if v <= 0:
            raise ValueError('Total budget must be greater than 0')
        return v

class AuctionConfig(BaseModel):
    base_price: float
    max_players_per_team: int
    total_budget_per_team: float
    auction_configured: bool
    auction_started: bool

    class Config:
        from_attributes = True

# Player Purchase DTOs
class PlayerPurchase(BaseModel):
    id: int
    team_season_id: int
    player_season_id: int
    purchase_price: float
    purchase_round: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Team Registration DTO
class TeamRegistrationCreate(BaseModel):
    teams: List[TeamCreate]

class TeamWithIconPlayer(BaseModel):
    team_id: int
    icon_player_id: int
