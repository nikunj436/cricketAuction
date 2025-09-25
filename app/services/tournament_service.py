"""
Tournament service for Cricket Auction API.

Handles tournament and season management business logic.
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.models.tournament import Tournament as TournamentModel, Season as SeasonModel
from app.dto.tournament_dto import Tournament, TournamentCreate, Season, SeasonCreate
from app.managers.validation_manager import ValidationManager


class TournamentService:
    """Service for tournament and season management operations."""
    
    @staticmethod
    def create_tournament(tournament_data: TournamentCreate, current_user: User, db: Session) -> TournamentModel:
        """
        Create a new tournament. No credit limit - organizers can create unlimited tournaments.
        """
        # Check if tournament with same name already exists for this organizer
        existing_tournament = db.query(TournamentModel).filter(
            TournamentModel.name == tournament_data.name,
            TournamentModel.created_by == current_user.id,
            TournamentModel.is_active == True
        ).first()
        
        if existing_tournament:
            raise HTTPException(
                status_code=400,
                detail=f"Tournament with name '{tournament_data.name}' already exists"
            )
        
        new_tournament = TournamentModel(
            name=tournament_data.name,
            description=tournament_data.description,
            location=tournament_data.location,
            created_by=current_user.id
        )
        db.add(new_tournament)
        db.commit()
        db.refresh(new_tournament)
        return new_tournament

    @staticmethod
    def create_season(tournament_id: int, season_data: SeasonCreate, current_user: User, db: Session) -> SeasonModel:
        """
        Create a new season under an existing tournament. Uses 1 auction credit.
        """
        # Check if organizer has credits
        ValidationManager.validate_auction_credits(current_user)
        
        # Verify tournament belongs to organizer
        tournament = ValidationManager.validate_tournament_ownership(db, tournament_id, current_user)
        
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

    @staticmethod
    def get_tournament_seasons(tournament_id: int, current_user: User, db: Session) -> List[SeasonModel]:
        """
        Get all seasons for a specific tournament, ordered by latest first.
        """
        # Verify tournament belongs to organizer
        tournament = ValidationManager.validate_tournament_ownership(db, tournament_id, current_user)
        
        seasons = db.query(SeasonModel).filter(
            SeasonModel.tournament_id == tournament_id
        ).order_by(SeasonModel.created_at.desc()).all()
        return seasons

    @staticmethod
    def get_my_seasons(current_user: User, db: Session) -> List[SeasonModel]:
        """
        Get all seasons created by the current organizer, ordered by latest first.
        """
        seasons = db.query(SeasonModel).filter(
            SeasonModel.created_by == current_user.id
        ).order_by(SeasonModel.created_at.desc()).all()
        return seasons

    @staticmethod
    def get_my_tournaments(current_user: User, db: Session) -> List[TournamentModel]:
        """
        Get all tournaments created by the current organizer, ordered by latest first.
        """
        tournaments = db.query(TournamentModel).filter(
            TournamentModel.created_by == current_user.id
        ).order_by(TournamentModel.created_at.desc()).all()
        return tournaments
