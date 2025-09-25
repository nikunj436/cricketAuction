from enum import Enum

class AuctionStatus(str, Enum):
    PENDING = "pending"           # Player available for auction
    SOLD = "sold"                # Player sold to a team
    UNSOLD = "unsold"            # Player not sold in current round
    ICON_PLAYER = "icon_player"  # Pre-assigned icon player
    OWNER = "owner"              # Team owner (not in auction)

class AuctionMode(str, Enum):
    RANDOM = "random"            # System randomly selects players
    MANUAL = "manual"            # Organizer inputs player ID
    FAST_ASSIGN = "fast_assign"  # Direct assignment without bidding
