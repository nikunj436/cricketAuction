"""
Data serializers for consistent API responses.
"""

from app.models.player import Player as PlayerModel


class PlayerSerializer:
    """Serializer for player data."""
    
    @staticmethod
    def serialize_player_data(player: PlayerModel) -> dict:
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
