"""
Validation manager for Cricket Auction API.

Handles all validation logic including ownership, auction status, and business rules.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User
from app.models.tournament import Tournament as TournamentModel, Season as SeasonModel


class ValidationManager:
    """Manager for handling various validation operations."""
    
    @staticmethod
    def validate_season_ownership(db: Session, season_id: int, current_user: User) -> SeasonModel:
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

    @staticmethod
    def validate_tournament_ownership(db: Session, tournament_id: int, current_user: User) -> TournamentModel:
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

    @staticmethod
    def validate_auction_started(season: SeasonModel) -> None:
        """
        Validate that auction has started for the season.
        Raises HTTPException if auction hasn't started.
        """
        if not season.auction_started:
            raise HTTPException(status_code=400, detail="Auction has not started yet")

    @staticmethod
    def validate_auction_credits(current_user: User) -> None:
        """
        Validate that organizer has available auction credits.
        Raises HTTPException if no credits available.
        """
        if current_user.auction_limit <= current_user.auctions_created:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits. You have used {current_user.auctions_created} out of {current_user.auction_limit} credits."
            )
