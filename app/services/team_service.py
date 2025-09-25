"""
Team service for Cricket Auction API.

Handles team registration and management business logic.
"""

from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.models.team import Team as TeamModel, TeamSeason as TeamSeasonModel
from app.dto.team_dto import (
    AuctionConfig, AuctionConfigCreate, TeamRegistrationCreate, TeamWithIconPlayer
)
from app.managers.validation_manager import ValidationManager
from app.managers.data_manager import DataManager


class TeamService:
    """Service for team management operations."""
    
    @staticmethod
    def configure_auction(season_id: int, config_data: AuctionConfigCreate, 
                         current_user: User, db: Session) -> AuctionConfig:
        """
        Configure auction settings for a season (base price, max players, budget).
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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

    @staticmethod
    def get_auction_config(season_id: int, current_user: User, db: Session) -> AuctionConfig:
        """
        Get auction configuration for a season.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
        return AuctionConfig(
            base_price=season.base_price,
            max_players_per_team=season.max_players_per_team,
            total_budget_per_team=season.total_budget_per_team,
            auction_configured=season.auction_configured,
            auction_started=season.auction_started
        )

    @staticmethod
    def register_teams_for_season(season_id: int, team_data: TeamRegistrationCreate, 
                                 current_user: User, db: Session) -> List[TeamSeasonModel]:
        """
        Register multiple teams for a season.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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

    @staticmethod
    def get_season_teams(season_id: int, current_user: User, db: Session) -> List[TeamSeasonModel]:
        """
        Get all teams registered for a season.
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
        team_seasons = db.query(TeamSeasonModel).filter(
            TeamSeasonModel.season_id == season_id,
            TeamSeasonModel.is_active == True
        ).all()
        
        return team_seasons

    @staticmethod
    def assign_icon_players(season_id: int, assignments: List[TeamWithIconPlayer], 
                           current_user: User, db: Session) -> dict:
        """
        Assign icon players to teams. Icon players are pre-assigned and won't go to auction.
        """
        # Verify season belongs to organizer
        season = ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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
            from app.models.player import PlayerSeason as PlayerSeasonModel
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
            DataManager.create_player_purchase(db, team_season, assignment.icon_player_id, Decimal('0'), is_icon_player=True)
            assigned_players.append(assignment.icon_player_id)
        
        db.commit()
        
        return {
            "message": f"Successfully assigned {len(assigned_players)} icon players",
            "assigned_players": assigned_players
        }
