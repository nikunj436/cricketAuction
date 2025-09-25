from enum import Enum

class BattingStyle(Enum):
    RIGHT_HANDED = "right_handed"
    LEFT_HANDED = "left_handed"

class BowlingStyle(Enum):
    RIGHT_ARM_FAST = "right_arm_fast"
    LEFT_ARM_FAST = "left_arm_fast"
    RIGHT_ARM_MEDIUM = "right_arm_medium"
    LEFT_ARM_MEDIUM = "left_arm_medium"
    RIGHT_ARM_SPIN = "right_arm_spin"
    LEFT_ARM_SPIN = "left_arm_spin"
    RIGHT_ARM_OFFBREAK = "right_arm_offbreak"
    LEFT_ARM_ORTHODOX = "left_arm_orthodox"

class PlayerRole(Enum):
    WICKETKEEPER = "wicketkeeper"
    BATSMAN = "batsman"
    BOWLER = "bowler"
    ALLROUNDER = "allrounder"
    WICKETKEEPER_BATSMAN = "wicketkeeper_batsman"
