from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.models import User
from app.dto.user_dto import User as UserSchema
from app.dto.tournament_dto import (
    Tournament, TournamentCreate, Season, SeasonCreate, 
    Player, PlayerCreate, PlayerSeason, PlayerSelectionUpdate
)
from app.dto.team_dto import (
    AuctionConfig, AuctionConfigCreate, TeamRegistrationCreate, TeamWithIconPlayer, TeamSeason
)
from app.dto.auction_dto import (
    AuctionStart, PlayerBid, ManualPlayerSelect, FastAssignment,
    AuctionPlayerResponse, TeamOverview, TeamDetails, AuctionPlayersList
)
from app.services import (
    TournamentService, PlayerService, TeamService, AuctionService, TrackingService
)

router = APIRouter()

# Dashboard and Profile endpoints
@router.get("/dashboard", response_model=UserSchema, tags=["Tournament Management"])
def read_user_dashboard(current_user: User = Depends(deps.get_current_user)):
    """
    Get the current logged-in user's dashboard info.
    """
    return current_user

@router.get("/profile", response_model=UserSchema, tags=["Tournament Management"])
def get_organizer_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get the current organizer's profile.
    """
    return current_user


# Tournament Management
@router.post("/tournaments", response_model=Tournament, tags=["Tournament Management"])
def create_tournament(
    tournament_data: TournamentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Create a new tournament. No credit limit - organizers can create unlimited tournaments.
    """
    return TournamentService.create_tournament(tournament_data, current_user, db)

@router.post("/tournaments/{tournament_id}/seasons", response_model=Season, tags=["Tournament Management"])
def create_season(
    tournament_id: int,
    season_data: SeasonCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Create a new season under an existing tournament. Uses 1 auction credit.
    """
    return TournamentService.create_season(tournament_id, season_data, current_user, db)

@router.get("/tournaments/{tournament_id}/seasons", response_model=List[Season], tags=["Tournament Management"])
def get_tournament_seasons(
    tournament_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all seasons for a specific tournament.
    """
    return TournamentService.get_tournament_seasons(tournament_id, current_user, db)

@router.get("/seasons", response_model=List[Season], tags=["Tournament Management"])
def get_my_seasons(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all seasons created by the current organizer.
    """
    return TournamentService.get_my_seasons(current_user, db)

@router.get("/tournaments", response_model=List[Tournament], tags=["Tournament Management"])
def get_my_tournaments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all tournaments created by the current organizer.
    """
    return TournamentService.get_my_tournaments(current_user, db)

# Player Management
@router.get("/players/search/{mobile}", response_model=Player, tags=["Player Management"])
def get_player_by_mobile(
    mobile: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Search for existing player data by mobile number for auto-fill functionality.
    """
    return PlayerService.get_player_by_mobile(mobile, db)

@router.post("/seasons/{season_id}/players", response_model=PlayerSeason, tags=["Player Management"])
def register_player(
    season_id: int,
    player_data: PlayerCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Register a player for a season.
    """
    return PlayerService.register_player(season_id, player_data, current_user, db)

@router.get("/seasons/{season_id}/players", response_model=List[PlayerSeason], tags=["Player Management"])
def get_season_players(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all players registered for a season.
    """
    return PlayerService.get_season_players(season_id, current_user, db)

@router.post("/seasons/{season_id}/close-registration", tags=["Player Management"])
def close_player_registration(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Close player registration for a season.
    """
    return PlayerService.close_player_registration(season_id, current_user, db)

@router.post("/seasons/{season_id}/select-players", tags=["Player Management"])
def select_players_for_auction(
    season_id: int,
    selection_data: PlayerSelectionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Select players for auction from registered players.
    """
    return PlayerService.select_players_for_auction(season_id, selection_data, current_user, db)

# Team Management
@router.post("/seasons/{season_id}/auction-config", response_model=AuctionConfig, tags=["Team Management"])
def configure_auction(
    season_id: int,
    config_data: AuctionConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Configure auction settings for a season.
    """
    return TeamService.configure_auction(season_id, config_data, current_user, db)

@router.get("/seasons/{season_id}/auction-config", response_model=AuctionConfig, tags=["Team Management"])
def get_auction_config(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get auction configuration for a season.
    """
    return TeamService.get_auction_config(season_id, current_user, db)

@router.post("/seasons/{season_id}/teams", response_model=List[TeamSeason], tags=["Team Management"])
def register_teams_for_season(
    season_id: int,
    team_data: TeamRegistrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Register multiple teams for a season.
    """
    return TeamService.register_teams_for_season(season_id, team_data, current_user, db)

@router.get("/seasons/{season_id}/teams", response_model=List[TeamSeason], tags=["Team Management"])
def get_season_teams(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all teams registered for a season.
    """
    return TeamService.get_season_teams(season_id, current_user, db)

@router.post("/seasons/{season_id}/assign-icon-players", tags=["Team Management"])
def assign_icon_players(
    season_id: int,
    assignments: List[TeamWithIconPlayer],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Assign icon players to teams.
    """
    return TeamService.assign_icon_players(season_id, assignments, current_user, db)

# Auction System
@router.post("/seasons/{season_id}/start-auction", tags=["Auction System"])
def start_auction(
    season_id: int,
    auction_config: AuctionStart,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Start the auction for a season.
    """
    return AuctionService.start_auction(season_id, auction_config, current_user, db)

@router.get("/seasons/{season_id}/next-player", response_model=AuctionPlayerResponse, tags=["Auction System"])
def get_next_auction_player(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get next random player for auction (RANDOM mode).
    """
    return AuctionService.get_next_auction_player(season_id, current_user, db)

@router.post("/seasons/{season_id}/manual-player", tags=["Auction System"])
def get_manual_auction_player(
    season_id: int,
    player_select: ManualPlayerSelect,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get specific player for auction (MANUAL mode).
    """
    return AuctionService.get_manual_auction_player(season_id, player_select, current_user, db)

@router.post("/seasons/{season_id}/bid-player", tags=["Auction System"])
def bid_on_player(
    season_id: int,
    bid_data: PlayerBid,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Process player bid - either sell to team or mark as unsold.
    """
    return AuctionService.bid_on_player(season_id, bid_data, current_user, db)

@router.post("/seasons/{season_id}/fast-assign", tags=["Auction System"])
def fast_assign_players(
    season_id: int,
    assignments: List[FastAssignment],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Fast assign multiple players to teams without bidding process.
    """
    return AuctionService.fast_assign_players(season_id, assignments, current_user, db)

@router.post("/seasons/{season_id}/start-next-round", tags=["Auction System"])
def start_next_auction_round(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Start next auction round with unsold players.
    """
    return AuctionService.start_next_auction_round(season_id, current_user, db)

# Team Tracking
@router.get("/seasons/{season_id}/teams-overview", response_model=List[TeamOverview], tags=["Team Tracking"])
def get_teams_overview(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get overview of all teams in season.
    """
    return TrackingService.get_teams_overview(season_id, current_user, db)

@router.get("/seasons/{season_id}/teams/{team_id}/details", response_model=TeamDetails, tags=["Team Tracking"])
def get_team_details(
    season_id: int,
    team_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get detailed view of a specific team.
    """
    return TrackingService.get_team_details(season_id, team_id, current_user, db)

@router.get("/seasons/{season_id}/auction-players", response_model=List[AuctionPlayersList], tags=["Team Tracking"])
def get_auction_players_list(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get list of all players selected for auction.
    """
    return TrackingService.get_auction_players_list(season_id, current_user, db)
