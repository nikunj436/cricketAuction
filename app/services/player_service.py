"""
Player service for Cricket Auction API.

Handles player registration and management business logic.
"""

from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.models.player import Player as PlayerModel, PlayerSeason as PlayerSeasonModel
from app.dto.tournament_dto import Player, PlayerCreate, PlayerSeason, PlayerSelectionUpdate
from app.managers.validation_manager import ValidationManager
from app.managers.auction_manager import AuctionManager


class PlayerService:
    """Service for player management operations."""
    
    @staticmethod
    def get_player_by_mobile(mobile: str, db: Session) -> PlayerModel:
        """
        Search for existing player data by mobile number for auto-fill functionality.
        """
        existing_player = db.query(PlayerModel).filter(
            PlayerModel.mobile == mobile,
            PlayerModel.is_active == True
        ).first()
        
        if not existing_player:
            raise HTTPException(status_code=404, detail="No player found with this mobile number")
        
        return existing_player

    @staticmethod
    def register_player(season_id: int, player_data: PlayerCreate, current_user: User, db: Session) -> PlayerSeasonModel:
        """
        Register a player for a season.
        Creates new player if doesn't exist, or links existing player to season.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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
            existing_player.player_role = AuctionManager.calculate_player_role(
                player_data.is_wicketkeeper,
                player_data.is_batsman,
                player_data.is_bowler
            )
            existing_player.updated_at = datetime.now()
            player = existing_player
        else:
            # Create new player
            player_role = AuctionManager.calculate_player_role(
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

    @staticmethod
    def get_season_players(season_id: int, current_user: User, db: Session) -> List[PlayerSeasonModel]:
        """
        Get all players registered for a season.
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
        player_seasons = db.query(PlayerSeasonModel).filter(
            PlayerSeasonModel.season_id == season_id,
            PlayerSeasonModel.is_active == True
        ).all()
        
        return player_seasons

    @staticmethod
    def close_player_registration(season_id: int, current_user: User, db: Session) -> dict:
        """
        Close player registration for a season.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
        season.registration_open = False
        db.commit()
        
        return {"message": "Player registration closed successfully"}

    @staticmethod
    def select_players_for_auction(season_id: int, selection_data: PlayerSelectionUpdate, 
                                 current_user: User, db: Session) -> dict:
        """
        Select players for auction from registered players.
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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
