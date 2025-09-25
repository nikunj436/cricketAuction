"""
Auction service for Cricket Auction API.

Handles auction management and bidding business logic.
"""

from typing import List
import random
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.models.player import PlayerSeason as PlayerSeasonModel
from app.models.team import TeamSeason as TeamSeasonModel
from app.dto.auction_dto import (
    AuctionStart, PlayerBid, ManualPlayerSelect, FastAssignment,
    AuctionPlayerResponse
)
from app.managers.validation_manager import ValidationManager
from app.managers.auction_manager import AuctionManager
from app.managers.data_manager import DataManager
from app.utils.serializers import PlayerSerializer
from app.enums.auction_status import AuctionStatus


class AuctionService:
    """Service for auction management operations."""
    
    @staticmethod
    def start_auction(season_id: int, auction_config: AuctionStart, 
                     current_user: User, db: Session) -> dict:
        """
        Start the auction for a season. Initialize all player statuses.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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

    @staticmethod
    def get_next_auction_player(season_id: int, current_user: User, db: Session) -> AuctionPlayerResponse:
        """
        Get next random player for auction (RANDOM mode).
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        ValidationManager.validate_auction_started(season)
        
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
        max_bid = AuctionManager.calculate_max_bid_for_player(db, season_id, season.base_price, season.max_players_per_team)
        
        return AuctionPlayerResponse(
            id=selected_player.id,
            player_id=selected_player.player_id,
            season_id=selected_player.season_id,
            auction_status=selected_player.auction_status,
            auction_round=selected_player.auction_round,
            player=PlayerSerializer.serialize_player_data(selected_player.player),
            max_bid_allowed=max_bid
        )

    @staticmethod
    def get_manual_auction_player(season_id: int, player_select: ManualPlayerSelect, 
                                 current_user: User, db: Session) -> AuctionPlayerResponse:
        """
        Get specific player for auction (MANUAL mode).
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        ValidationManager.validate_auction_started(season)
        
        # Get the specific player
        player_season = db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.player_id == player_select.player_id,
            PlayerSeasonModel.auction_status == AuctionStatus.PENDING
        ).first()
        
        if not player_season:
            raise HTTPException(status_code=404, detail="Player not found or not available for auction")
        
        # Calculate maximum bid allowed
        max_bid = AuctionManager.calculate_max_bid_for_player(db, season_id, season.base_price, season.max_players_per_team)
        
        return AuctionPlayerResponse(
            id=player_season.id,
            player_id=player_season.player_id,
            season_id=player_season.season_id,
            auction_status=player_season.auction_status,
            auction_round=player_season.auction_round,
            player=PlayerSerializer.serialize_player_data(player_season.player),
            max_bid_allowed=max_bid
        )

    @staticmethod
    def bid_on_player(season_id: int, bid_data: PlayerBid, current_user: User, db: Session) -> dict:
        """
        Process player bid - either sell to team or mark as unsold.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        ValidationManager.validate_auction_started(season)
        
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
            validation = AuctionManager.validate_team_budget(db, team_season, bid_data.bid_amount, season.base_price)
            if not validation["can_bid"]:
                raise HTTPException(status_code=400, detail=validation["reason"])
            
            # Create player purchase record and update team
            DataManager.create_player_purchase(db, team_season, bid_data.player_id, bid_data.bid_amount)
            
            # Update player status
            player_season.auction_status = AuctionStatus.SOLD
            
            message = f"Player sold to {team_season.team.name} for ₹{bid_data.bid_amount:,.2f}"
        else:
            # Mark as unsold
            player_season.auction_status = AuctionStatus.UNSOLD
            message = "Player marked as unsold"
        
        db.commit()
        
        return {"message": message}

    @staticmethod
    def fast_assign_players(season_id: int, assignments: List[FastAssignment], 
                           current_user: User, db: Session) -> dict:
        """
        Fast assign multiple players to teams without bidding process.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        ValidationManager.validate_auction_started(season)
        
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
            validation = AuctionManager.validate_team_budget(db, team_season, assignment.price, season.base_price)
            if not validation["can_bid"]:
                continue  # Skip if budget validation fails
            
            # Create player purchase record and update team
            DataManager.create_player_purchase(db, team_season, assignment.player_id, assignment.price)
            
            # Update player status
            player_season.auction_status = AuctionStatus.SOLD
            assigned_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully assigned {assigned_count} players",
            "assigned_count": assigned_count
        }

    @staticmethod
    def start_next_auction_round(season_id: int, current_user: User, db: Session) -> dict:
        """
        Start next auction round with unsold players.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        ValidationManager.validate_auction_started(season)
        
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
