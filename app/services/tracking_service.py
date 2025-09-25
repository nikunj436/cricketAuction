"""
Tracking service for Cricket Auction API.

Handles team tracking and reporting business logic.
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.models.player import Player as PlayerModel, PlayerSeason as PlayerSeasonModel
from app.models.team import TeamSeason as TeamSeasonModel, PlayerPurchase as PlayerPurchaseModel
from app.dto.auction_dto import TeamOverview, TeamDetails, AuctionPlayersList
from app.managers.validation_manager import ValidationManager


class TrackingService:
    """Service for team tracking and reporting operations."""
    
    @staticmethod
    def get_teams_overview(season_id: int, current_user: User, db: Session) -> List[TeamOverview]:
        """
        Get overview of all teams in season (players count, budget, etc.).
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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

    @staticmethod
    def get_team_details(season_id: int, team_id: int, current_user: User, db: Session) -> TeamDetails:
        """
        Get detailed view of a specific team (all players list).
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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

    @staticmethod
    def get_auction_players_list(season_id: int, current_user: User, db: Session) -> List[AuctionPlayersList]:
        """
        Get list of all players selected for auction with their IDs (for organizer reference).
        """
        # Verify season belongs to organizer
        ValidationManager.validate_season_ownership(db, season_id, current_user)
        
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
