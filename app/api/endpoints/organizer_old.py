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
    AuctionConfig, AuctionConfigCreate, TeamRegistrationCreate, TeamWithIconPlayer
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

# Season Management
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
    # Check if organizer has credits
    if current_user.auction_limit <= current_user.auctions_created:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient credits. You have used {current_user.auctions_created} out of {current_user.auction_limit} credits."
        )
    
    # Verify tournament exists and belongs to organizer
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id,
        TournamentModel.created_by == current_user.id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found or access denied")
    
    # Create season
    new_season = SeasonModel(
        name=season_data.name,
        year=season_data.year,
        tournament_id=tournament_id,
        created_by=current_user.id
    )
    db.add(new_season)
    
    # Deduct credit
    current_user.auctions_created += 1
    
    db.commit()
    db.refresh(new_season)
    return new_season

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
    Returns the player record for the given mobile number.
    """
    # Find player with this mobile number
    existing_player = db.query(PlayerModel).filter(
        PlayerModel.mobile == mobile,
        PlayerModel.is_active == True
    ).first()
    
    if not existing_player:
        raise HTTPException(status_code=404, detail="No player found with this mobile number")
    
    return existing_player

@router.post("/seasons/{season_id}/players", response_model=PlayerSeason, tags=["Player Management"])
def register_player(
    season_id: int,
    player_data: PlayerCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Register a player for a season.
    Creates new player if doesn't exist, or links existing player to season.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    if not season.registration_open:
        raise HTTPException(status_code=400, detail="Registration is closed for this season")
    
    # Check if player already registered in this season
    existing_player_season = db.query(PlayerSeasonModel).join(PlayerModel).filter(
        PlayerModel.mobile == player_data.mobile,
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.is_active == True
    ).first()
    
    if existing_player_season:
        raise HTTPException(
            status_code=400, 
            detail=f"Player with mobile {player_data.mobile} is already registered in this season"
        )
    
    # Check if player exists in database
    existing_player = db.query(PlayerModel).filter(
        PlayerModel.mobile == player_data.mobile,
        PlayerModel.is_active == True
    ).first()
    
    if existing_player:
        # Update existing player data if needed
        existing_player.first_name = player_data.first_name
        existing_player.last_name = player_data.last_name
        existing_player.village = player_data.village
        existing_player.photo_url = player_data.photo_url or existing_player.photo_url
        existing_player.is_wicketkeeper = player_data.is_wicketkeeper
        existing_player.is_batsman = player_data.is_batsman
        existing_player.is_bowler = player_data.is_bowler
        existing_player.batting_style = player_data.batting_style
        existing_player.bowling_style = player_data.bowling_style
        existing_player.player_role = _calculate_player_role(
            player_data.is_wicketkeeper,
            player_data.is_batsman,
            player_data.is_bowler
        )
        existing_player.updated_at = datetime.now()
        player = existing_player
    else:
        # Create new player
        player_role = _calculate_player_role(
            player_data.is_wicketkeeper,
            player_data.is_batsman,
            player_data.is_bowler
        )
        
        player = PlayerModel(
            first_name=player_data.first_name,
            last_name=player_data.last_name,
            village=player_data.village,
            mobile=player_data.mobile,
            photo_url=player_data.photo_url,
            is_wicketkeeper=player_data.is_wicketkeeper,
            is_batsman=player_data.is_batsman,
            is_bowler=player_data.is_bowler,
            batting_style=player_data.batting_style,
            bowling_style=player_data.bowling_style,
            player_role=player_role
        )
        db.add(player)
        db.flush()  # Get player ID
    
    # Create player-season relationship
    player_season = PlayerSeasonModel(
        player_id=player.id,
        season_id=season_id
    )
    
    db.add(player_season)
    db.commit()
    db.refresh(player_season)
    return player_season

@router.get("/seasons/{season_id}/players", response_model=List[PlayerSeason], tags=["Player Management"])
def get_season_players(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all players registered for a season.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    player_seasons = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.is_active == True
    ).all()
    
    return player_seasons

@router.post("/seasons/{season_id}/close-registration", tags=["Player Management"])
def close_player_registration(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Close player registration for a season.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    season.registration_open = False
    db.commit()
    
    return {"message": "Player registration closed successfully"}

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
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    # Reset all players selection status for this season
    db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id
    ).update({"is_selected_for_auction": False})
    
    # Select specified players
    if selection_data.player_ids:
        db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.player_id.in_(selection_data.player_ids),
            PlayerSeasonModel.season_id == season_id
        ).update({"is_selected_for_auction": True})
    
    db.commit()
    
    return {"message": f"Selected {len(selection_data.player_ids)} players for auction"}

# Team Management
@router.post("/seasons/{season_id}/auction-config", response_model=AuctionConfig, tags=["Team Management"])
def configure_auction(
    season_id: int,
    config_data: AuctionConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Configure auction settings for a season (base price, max players, budget).
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    if season.auction_started:
        raise HTTPException(status_code=400, detail="Cannot modify auction config after auction has started")
    
    # Update auction configuration
    season.base_price = config_data.base_price
    season.max_players_per_team = config_data.max_players_per_team
    season.total_budget_per_team = config_data.total_budget_per_team
    season.auction_configured = True
    
    db.commit()
    db.refresh(season)
    
    return AuctionConfig(
        base_price=season.base_price,
        max_players_per_team=season.max_players_per_team,
        total_budget_per_team=season.total_budget_per_team,
        auction_configured=season.auction_configured,
        auction_started=season.auction_started
    )

@router.get("/seasons/{season_id}/auction-config", response_model=AuctionConfig, tags=["Team Management"])
def get_auction_config(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get auction configuration for a season.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    return AuctionConfig(
        base_price=season.base_price,
        max_players_per_team=season.max_players_per_team,
        total_budget_per_team=season.total_budget_per_team,
        auction_configured=season.auction_configured,
        auction_started=season.auction_started
    )

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
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    if not season.auction_configured:
        raise HTTPException(status_code=400, detail="Please configure auction settings before registering teams")
    
    if season.auction_started:
        raise HTTPException(status_code=400, detail="Cannot register teams after auction has started")
    
    created_team_seasons = []
    
    for team_create in team_data.teams:
        # Check if team already exists
        existing_team = db.query(TeamModel).filter(
            TeamModel.name == team_create.name
        ).first()
        
        if existing_team:
            team = existing_team
        else:
            # Create new team
            team = TeamModel(
                name=team_create.name,
                logo_url=team_create.logo_url,
                owner_name=team_create.owner_name
            )
            db.add(team)
            db.flush()  # Get team ID
        
        # Check if team already registered for this season
        existing_team_season = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.team_id == team.id,
            TeamSeasonModel.season_id == season_id
        ).first()
        
        if existing_team_season:
            raise HTTPException(
                status_code=400,
                detail=f"Team '{team.name}' is already registered for this season"
            )
        
        # Create team-season relationship
        team_season = TeamSeasonModel(
            team_id=team.id,
            season_id=season_id,
            total_budget=season.total_budget_per_team,
            remaining_budget=season.total_budget_per_team,
            max_players=season.max_players_per_team
        )
        
        db.add(team_season)
        created_team_seasons.append(team_season)
    
    db.commit()
    
    # Refresh all created team seasons
    for team_season in created_team_seasons:
        db.refresh(team_season)
    
    return created_team_seasons

@router.get("/seasons/{season_id}/teams", response_model=List[TeamSeason], tags=["Team Management"])
def get_season_teams(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get all teams registered for a season.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    team_seasons = db.query(TeamSeasonModel).filter(
        TeamSeasonModel.season_id == season_id,
        TeamSeasonModel.is_active == True
    ).all()
    
    return team_seasons

@router.post("/seasons/{season_id}/assign-icon-players", tags=["Team Management"])
def assign_icon_players(
    season_id: int,
    assignments: List[TeamWithIconPlayer],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Assign icon players to teams. Icon players are pre-assigned and won't go to auction.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    if season.auction_started:
        raise HTTPException(status_code=400, detail="Cannot assign icon players after auction has started")
    
    assigned_players = []
    
    for assignment in assignments:
        # Verify team exists in this season
        team_season = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.team_id == assignment.team_id,
            TeamSeasonModel.season_id == season_id
        ).first()
        
        if not team_season:
            raise HTTPException(
                status_code=404,
                detail=f"Team ID {assignment.team_id} not found in this season"
            )
        
        # Verify player is selected for auction
        player_season = db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.player_id == assignment.icon_player_id,
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.is_selected_for_auction == True
        ).first()
        
        if not player_season:
            raise HTTPException(
                status_code=404,
                detail=f"Player ID {assignment.icon_player_id} not found or not selected for auction"
            )
        
        # Check if player is already assigned as icon player
        existing_assignment = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.icon_player_id == assignment.icon_player_id,
            TeamSeasonModel.season_id == season_id
        ).first()
        
        if existing_assignment:
            raise HTTPException(
                status_code=400,
                detail=f"Player ID {assignment.icon_player_id} is already assigned as icon player"
            )
        
        # Assign icon player
        team_season.icon_player_id = assignment.icon_player_id
        team_season.current_players = 1  # Icon player counts as 1 player
        
        # Create player purchase record
        _create_player_purchase(db, team_season, assignment.icon_player_id, Decimal('0'), is_icon_player=True)
        assigned_players.append(assignment.icon_player_id)
    
    db.commit()
    
    return {
        "message": f"Successfully assigned {len(assigned_players)} icon players",
        "assigned_players": assigned_players
    }

# Auction Management
@router.post("/seasons/{season_id}/start-auction", tags=["Auction System"])
def start_auction(
    season_id: int,
    auction_config: AuctionStart,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Start the auction for a season. Initialize all player statuses.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    if not season.auction_configured:
        raise HTTPException(status_code=400, detail="Please configure auction settings first")
    
    if season.auction_started:
        raise HTTPException(status_code=400, detail="Auction has already started")
    
    # Check if teams are registered
    team_count = db.query(TeamSeasonModel).filter(
        TeamSeasonModel.season_id == season_id,
        TeamSeasonModel.is_active == True
    ).count()
    
    if team_count == 0:
        raise HTTPException(status_code=400, detail="No teams registered for this season")
    
    # Start auction
    season.auction_started = True
    season.auction_mode = auction_config.auction_mode
    season.current_auction_round = 1
    
    # Update icon players status
    icon_player_ids = db.query(TeamSeasonModel.icon_player_id).filter(
        TeamSeasonModel.season_id == season_id,
        TeamSeasonModel.icon_player_id.isnot(None)
    ).all()
    
    if icon_player_ids:
        icon_ids = [pid[0] for pid in icon_player_ids]
        db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.player_id.in_(icon_ids)
        ).update({"auction_status": AuctionStatus.ICON_PLAYER})
    
    # Set all other selected players to PENDING status
    db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.is_selected_for_auction == True,
        PlayerSeasonModel.auction_status == AuctionStatus.PENDING
    ).update({"auction_status": AuctionStatus.PENDING, "auction_round": 1})
    
    db.commit()
    
    return {
        "message": "Auction started successfully",
        "auction_mode": season.auction_mode,
        "current_round": season.current_auction_round,
        "total_teams": team_count
    }

@router.get("/seasons/{season_id}/next-player", response_model=AuctionPlayerResponse, tags=["Auction System"])
def get_next_auction_player(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get next random player for auction (RANDOM mode).
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    _validate_auction_started(season)
    
    # Get pending players for current round
    pending_players = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.auction_status == AuctionStatus.PENDING,
        PlayerSeasonModel.auction_round == season.current_auction_round
    ).all()
    
    if not pending_players:
        # Check if there are unsold players from previous rounds
        unsold_players = db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.auction_status == AuctionStatus.UNSOLD
        ).all()
        
        if unsold_players:
            return {
                "message": "No pending players. Start next round with unsold players?",
                "action_required": "start_next_round"
            }
        else:
            return {
                "message": "Auction completed! All players have been processed.",
                "action_required": "auction_complete"
            }
    
    # Randomly select a player
    selected_player = random.choice(pending_players)
    
    # Calculate maximum bid allowed for each team
    max_bid = _calculate_max_bid_for_player(db, season_id, season.base_price, season.max_players_per_team)
    
    return AuctionPlayerResponse(
        id=selected_player.id,
        player_id=selected_player.player_id,
        season_id=selected_player.season_id,
        auction_status=selected_player.auction_status,
        auction_round=selected_player.auction_round,
        player=_serialize_player_data(selected_player.player),
        max_bid_allowed=max_bid
    )

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
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    _validate_auction_started(season)
    
    # Get the specific player
    player_season = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.player_id == player_select.player_id,
        PlayerSeasonModel.auction_status == AuctionStatus.PENDING
    ).first()
    
    if not player_season:
        raise HTTPException(status_code=404, detail="Player not found or not available for auction")
    
    # Calculate maximum bid allowed
    max_bid = _calculate_max_bid_for_player(db, season_id, season.base_price, season.max_players_per_team)
    
    return AuctionPlayerResponse(
        id=player_season.id,
        player_id=player_season.player_id,
        season_id=player_season.season_id,
        auction_status=player_season.auction_status,
        auction_round=player_season.auction_round,
        player=_serialize_player_data(player_season.player),
        max_bid_allowed=max_bid
    )

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
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    _validate_auction_started(season)
    
    # Get player season record
    player_season = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.player_id == bid_data.player_id,
        PlayerSeasonModel.auction_status == AuctionStatus.PENDING
    ).first()
    
    if not player_season:
        raise HTTPException(status_code=404, detail="Player not found or not available for bidding")
    
    if bid_data.is_sold:
        # Validate bid amount
        if bid_data.bid_amount < season.base_price:
            raise HTTPException(
                status_code=400,
                detail=f"Bid amount must be at least base price of {season.base_price}"
            )
        
        # Get team season record
        team_season = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.team_id == bid_data.team_id,
            TeamSeasonModel.season_id == season_id
        ).first()
        
        if not team_season:
            raise HTTPException(status_code=404, detail="Team not found in this season")
        
        # Validate budget and player limits
        validation = _validate_team_budget(db, team_season, bid_data.bid_amount, season.base_price)
        if not validation["can_bid"]:
            raise HTTPException(status_code=400, detail=validation["reason"])
        
        # Create player purchase record and update team
        _create_player_purchase(db, team_season, bid_data.player_id, bid_data.bid_amount)
        
        # Update player status
        player_season.auction_status = AuctionStatus.SOLD
        
        message = f"Player sold to {team_season.team.name} for ₹{bid_data.bid_amount:,.2f}"
    else:
        # Mark as unsold
        player_season.auction_status = AuctionStatus.UNSOLD
        message = "Player marked as unsold"
    
    db.commit()
    
    return {"message": message}

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
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    _validate_auction_started(season)
    
    assigned_count = 0
    
    for assignment in assignments:
        # Get player season record
        player_season = db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.player_id == assignment.player_id,
            PlayerSeasonModel.auction_status.in_([AuctionStatus.PENDING, AuctionStatus.UNSOLD])
        ).first()
        
        if not player_season:
            continue  # Skip if player not available
        
        # Get team season record
        team_season = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.team_id == assignment.team_id,
            TeamSeasonModel.season_id == season_id
        ).first()
        
        if not team_season:
            continue  # Skip if team not found
        
        # Validate budget and player limits
        validation = _validate_team_budget(db, team_season, assignment.price, season.base_price)
        if not validation["can_bid"]:
            continue  # Skip if budget validation fails
        
        # Create player purchase record and update team
        _create_player_purchase(db, team_season, assignment.player_id, assignment.price)
        
        # Update player status
        player_season.auction_status = AuctionStatus.SOLD
        assigned_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully assigned {assigned_count} players",
        "assigned_count": assigned_count
    }

@router.post("/seasons/{season_id}/start-next-round", tags=["Auction System"])
def start_next_auction_round(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Start next auction round with unsold players.
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    _validate_auction_started(season)
    
    # Move unsold players to next round
    next_round = season.current_auction_round + 1
    
    updated_count = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.auction_status == AuctionStatus.UNSOLD
    ).update({
        "auction_status": AuctionStatus.PENDING,
        "auction_round": next_round
    })
    
    if updated_count == 0:
        raise HTTPException(status_code=400, detail="No unsold players to move to next round")
    
    # Update season round
    season.current_auction_round = next_round
    
    db.commit()
    
    return {
        "message": f"Started round {next_round} with {updated_count} players",
        "round_number": next_round,
        "players_count": updated_count
    }

# Team Overview and Details APIs
@router.get("/seasons/{season_id}/teams-overview", response_model=List[TeamOverview], tags=["Team Tracking"])
def get_teams_overview(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get overview of all teams in season (players count, budget, etc.).
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    team_seasons = db.query(TeamSeasonModel).filter(
        TeamSeasonModel.season_id == season_id,
        TeamSeasonModel.is_active == True
    ).all()
    
    teams_overview = []
    for team_season in team_seasons:
        icon_player_name = None
        if team_season.icon_player_id:
            icon_player = db.query(PlayerModel).filter(
                PlayerModel.id == team_season.icon_player_id
            ).first()
            if icon_player:
                icon_player_name = f"{icon_player.first_name} {icon_player.last_name}"
        
        teams_overview.append(TeamOverview(
            team_id=team_season.team_id,
            team_name=team_season.team.name,
            owner_name=team_season.team.owner_name,
            logo_url=team_season.team.logo_url,
            current_players=team_season.current_players,
            max_players=team_season.max_players,
            remaining_budget=team_season.remaining_budget,
            total_budget=team_season.total_budget,
            icon_player_name=icon_player_name
        ))
    
    return teams_overview

@router.get("/seasons/{season_id}/teams/{team_id}/details", response_model=TeamDetails, tags=["Team Tracking"])
def get_team_details(
    season_id: int,
    team_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get detailed view of a specific team (all players list).
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    # Get team season record
    team_season = db.query(TeamSeasonModel).filter(
        TeamSeasonModel.team_id == team_id,
        TeamSeasonModel.season_id == season_id
    ).first()
    
    if not team_season:
        raise HTTPException(status_code=404, detail="Team not found in this season")
    
    # Get all players purchased by this team
    player_purchases = db.query(PlayerPurchaseModel).filter(
        PlayerPurchaseModel.team_season_id == team_season.id,
        PlayerPurchaseModel.is_active == True
    ).all()
    
    players_list = []
    for purchase in player_purchases:
        player = purchase.player
        players_list.append({
            "id": player.id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "village": player.village,
            "mobile": player.mobile,
            "player_role": player.player_role.value,
            "batting_style": player.batting_style.value if player.batting_style else None,
            "bowling_style": player.bowling_style.value if player.bowling_style else None,
            "photo_url": player.photo_url,
            "purchase_price": float(purchase.purchase_price),
            "is_icon_player": purchase.is_icon_player,
            "purchased_at": purchase.purchased_at
        })
    
    return TeamDetails(
        team_id=team_season.team_id,
        team_name=team_season.team.name,
        owner_name=team_season.team.owner_name,
        logo_url=team_season.team.logo_url,
        current_players=team_season.current_players,
        max_players=team_season.max_players,
        remaining_budget=team_season.remaining_budget,
        total_budget=team_season.total_budget,
        players=players_list
    )

@router.get("/seasons/{season_id}/auction-players", response_model=List[AuctionPlayersList], tags=["Team Tracking"])
def get_auction_players_list(
    season_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_organizer)
):
    """
    Get list of all players selected for auction with their IDs (for organizer reference).
    """
    # Verify season belongs to organizer
    season = _validate_season_ownership(db, season_id, current_user)
    
    # Get all players selected for auction
    player_seasons = db.query(PlayerSeasonModel).filter(
        PlayerSeasonModel.season_id == season_id,
        PlayerSeasonModel.is_selected_for_auction == True,
        PlayerSeasonModel.is_active == True
    ).all()
    
    players_list = []
    for ps in player_seasons:
        player = ps.player
        players_list.append(AuctionPlayersList(
            player_id=player.id,
            first_name=player.first_name,
            last_name=player.last_name,
            village=player.village,
            mobile=player.mobile,
            player_role=player.player_role.value,
            batting_style=player.batting_style.value if player.batting_style else None,
            bowling_style=player.bowling_style.value if player.bowling_style else None,
            auction_status=ps.auction_status,
            auction_round=ps.auction_round
        ))
    
    return players_list

# Helper Functions
def _validate_season_ownership(db: Session, season_id: int, current_user: User) -> SeasonModel:
    """
    Validate that the season exists and belongs to the current organizer.
    Returns the season object if valid, raises HTTPException otherwise.
    """
    season = db.query(SeasonModel).filter(
        SeasonModel.id == season_id,
        SeasonModel.created_by == current_user.id
    ).first()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found or access denied")
    
    return season

def _validate_tournament_ownership(db: Session, tournament_id: int, current_user: User) -> TournamentModel:
    """
    Validate that the tournament exists and belongs to the current organizer.
    Returns the tournament object if valid, raises HTTPException otherwise.
    """
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id,
        TournamentModel.created_by == current_user.id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found or access denied")
    
    return tournament

def _validate_auction_started(season: SeasonModel) -> None:
    """
    Validate that auction has started for the season.
    Raises HTTPException if auction hasn't started.
    """
    if not season.auction_started:
        raise HTTPException(status_code=400, detail="Auction has not started yet")

def _serialize_player_data(player: PlayerModel) -> dict:
    """
    Serialize player data into a consistent dictionary format.
    """
    return {
        "id": player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "village": player.village,
        "mobile": player.mobile,
        "player_role": player.player_role.value,
        "batting_style": player.batting_style.value if player.batting_style else None,
        "bowling_style": player.bowling_style.value if player.bowling_style else None,
        "photo_url": player.photo_url
    }

def _create_player_purchase(db: Session, team_season: TeamSeasonModel, player_id: int, 
                           purchase_price: Decimal, is_icon_player: bool = False) -> PlayerPurchaseModel:
    """
    Create a player purchase record and update team budget/player count.
    """
    # Create player purchase record
    player_purchase = PlayerPurchaseModel(
        team_season_id=team_season.id,
        player_id=player_id,
        purchase_price=purchase_price,
        is_icon_player=is_icon_player
    )
    
    # Update team budget and player count
    team_season.remaining_budget -= purchase_price
    team_season.current_players += 1
    
    db.add(player_purchase)
    return player_purchase

def _calculate_max_bid_for_player(db: Session, season_id: int, base_price: Decimal, max_players: int) -> Decimal:
    """
    Calculate maximum bid amount any team can place for a player.
    """
    # Get all teams and their current status
    team_seasons = db.query(TeamSeasonModel).filter(
        TeamSeasonModel.season_id == season_id,
        TeamSeasonModel.is_active == True
    ).all()
    
    max_possible_bid = Decimal('0')
    
    for team_season in team_seasons:
        validation = _validate_team_budget(db, team_season, team_season.remaining_budget, base_price)
        if validation["can_bid"] and validation["max_bid_amount"] > max_possible_bid:
            max_possible_bid = validation["max_bid_amount"]
    
    return max_possible_bid

def _validate_team_budget(db: Session, team_season: TeamSeasonModel, bid_amount: Decimal, base_price: Decimal) -> dict:
    """
    Validate if team can afford the bid considering future player requirements.
    """
    # Check if team has reached player limit
    if team_season.current_players >= team_season.max_players:
        return {
            "can_bid": False,
            "max_bid_amount": Decimal('0'),
            "reason": "Team has reached maximum player limit"
        }
    
    # Check if team has enough budget for this bid
    if bid_amount > team_season.remaining_budget:
        return {
            "can_bid": False,
            "max_bid_amount": Decimal('0'),
            "reason": "Insufficient budget for this bid"
        }
    
    # Calculate remaining players needed
    remaining_players_needed = team_season.max_players - team_season.current_players - 1  # -1 for current player
    
    # Calculate minimum budget needed for remaining players
    min_budget_for_remaining = remaining_players_needed * base_price
    
    # Calculate maximum bid this team can place
    max_bid_amount = team_season.remaining_budget - min_budget_for_remaining
    
    if max_bid_amount < base_price:
        return {
            "can_bid": False,
            "max_bid_amount": Decimal('0'),
            "reason": f"Need to reserve ₹{min_budget_for_remaining} for {remaining_players_needed} more players"
        }
    
    if bid_amount > max_bid_amount:
        return {
            "can_bid": False,
            "max_bid_amount": max_bid_amount,
            "reason": f"Maximum bid allowed is ₹{max_bid_amount} (need to reserve budget for remaining players)"
        }
    
    return {
        "can_bid": True,
        "max_bid_amount": max_bid_amount,
        "reason": None
    }

def _calculate_player_role(is_wicketkeeper: bool, is_batsman: bool, is_bowler: bool) -> PlayerRole:
    """
    Auto-calculate player role based on selected skills.
    """
    if is_wicketkeeper and is_batsman:
        return PlayerRole.WICKETKEEPER_BATSMAN
    elif is_wicketkeeper:
        return PlayerRole.WICKETKEEPER
    elif is_batsman and is_bowler:
        return PlayerRole.ALLROUNDER
    elif is_batsman:
        return PlayerRole.BATSMAN
    elif is_bowler:
        return PlayerRole.BOWLER
    else:
        # Default to batsman if no role selected
        return PlayerRole.BATSMAN