"""
Auction manager for Cricket Auction API.

Handles auction-specific calculations and validations.
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.team import TeamSeason as TeamSeasonModel
from app.enums.player_type import PlayerRole


class AuctionManager:
    """Manager for auction-related calculations and operations."""
    
    @staticmethod
    def calculate_max_bid_for_player(db: Session, season_id: int, base_price: Decimal, max_players: int) -> Decimal:
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
            validation = AuctionManager.validate_team_budget(db, team_season, team_season.remaining_budget, base_price)
            if validation["can_bid"] and validation["max_bid_amount"] > max_possible_bid:
                max_possible_bid = validation["max_bid_amount"]
        
        return max_possible_bid

    @staticmethod
    def validate_team_budget(db: Session, team_season: TeamSeasonModel, bid_amount: Decimal, base_price: Decimal) -> dict:
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

    @staticmethod
    def calculate_player_role(is_wicketkeeper: bool, is_batsman: bool, is_bowler: bool) -> PlayerRole:
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
