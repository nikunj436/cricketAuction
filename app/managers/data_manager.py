"""
Data manager for Cricket Auction API.

Handles database operations and data persistence.
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.team import TeamSeason as TeamSeasonModel, PlayerPurchase as PlayerPurchaseModel


class DataManager:
    """Manager for database operations and data persistence."""
    
    @staticmethod
    def create_player_purchase(db: Session, team_season: TeamSeasonModel, player_id: int, 
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
