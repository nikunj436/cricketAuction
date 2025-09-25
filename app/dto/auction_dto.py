from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.enums.auction_status import AuctionStatus, AuctionMode

# Auction DTOs
class AuctionStart(BaseModel):
    auction_mode: AuctionMode = AuctionMode.RANDOM

class PlayerBid(BaseModel):
    player_id: int
    team_id: int
    bid_amount: Decimal
    is_sold: bool = True  # True if sold, False if unsold

    @field_validator('bid_amount')
    @classmethod
    def validate_bid_amount(cls, v):
        if v < 0:
            raise ValueError('Bid amount cannot be negative')
        return v

class ManualPlayerSelect(BaseModel):
    player_id: int

class FastAssignment(BaseModel):
    player_id: int
    team_id: int
    price: Decimal

class AuctionPlayerResponse(BaseModel):
    id: int
    player_id: int
    season_id: int
    auction_status: AuctionStatus
    auction_round: int
    player: dict  # Player details
    max_bid_allowed: Optional[Decimal] = None  # Maximum bid this player can receive

    class Config:
        from_attributes = True

class TeamOverview(BaseModel):
    team_id: int
    team_name: str
    owner_name: str
    logo_url: Optional[str]
    current_players: int
    max_players: int
    remaining_budget: Decimal
    total_budget: Decimal
    icon_player_name: Optional[str] = None

class TeamDetails(BaseModel):
    team_id: int
    team_name: str
    owner_name: str
    logo_url: Optional[str]
    current_players: int
    max_players: int
    remaining_budget: Decimal
    total_budget: Decimal
    players: List[dict]  # List of all players in team

class AuctionPlayersList(BaseModel):
    player_id: int
    first_name: str
    last_name: str
    village: str
    mobile: str
    player_role: str
    batting_style: Optional[str]
    bowling_style: Optional[str]
    auction_status: AuctionStatus
    auction_round: int

class BudgetValidation(BaseModel):
    team_id: int
    can_bid: bool
    max_bid_amount: Decimal
    reason: Optional[str] = None

class AuctionRoundSummary(BaseModel):
    round_number: int
    total_players: int
    sold_players: int
    unsold_players: int
    pending_players: int
