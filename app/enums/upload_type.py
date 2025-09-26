import enum


class UploadType(str, enum.Enum):
    PLAYER_PHOTO = "player_photo"
    TEAM_LOGO = "team_logo"
    TOURNAMENT_LOGO = "tournament_logo"
