from unicodedata import category
from pydantic import BaseModel, field_validator, HttpUrl, model_validator
from typing import Optional, List
from datetime import datetime
from app.enums.player_type import BattingStyle, BowlingStyle, PlayerRole

# Tournament DTOs
class TournamentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    logo: Optional[HttpUrl] = None 
    class Config:
        from_attributes = True

class TournamentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    logo: Optional[HttpUrl] = None

    class Config:
        from_attributes = True

# Season DTOs
class SeasonCreate(BaseModel):
    name: str
    year: int

class Season(BaseModel):
    id: int
    name: str
    year: int
    tournament_id: int
    created_by: int
    created_at: datetime
    registration_open: bool
    is_active: bool
    tournament: TournamentResponse

    class Config:
        from_attributes = True

# Player DTOs
class PlayerCreate(BaseModel):
    first_name: str
    last_name: str
    village: str
    mobile: str
    photo_url: Optional[str] = None
    is_wicketkeeper: bool = False
    is_batsman: bool = False
    is_bowler: bool = False
    batting_style: Optional[BattingStyle] = None
    bowling_style: Optional[BowlingStyle] = None

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Mobile number must be at least 10 digits')
        return v.strip()

class Player(BaseModel):
    id: int
    first_name: str
    last_name: str
    village: str
    mobile: str
    photo_url: Optional[str] = None
    is_wicketkeeper: bool
    is_batsman: bool
    is_bowler: bool
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    player_role: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Player Season DTOs
class PlayerSeason(BaseModel):
    id: int
    player_id: int
    season_id: int
    is_selected_for_auction: bool
    auction_status: str
    auction_round: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Player Selection DTO
class PlayerSelectionUpdate(BaseModel):
    player_ids: List[int]  # List of player IDs to select for auction
