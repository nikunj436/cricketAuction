import enum


class TournamentCategory(str, enum.Enum):
    COLLEGE = "College"
    COMMUNITY = "Community"
    DISTRICT = "District"
    NATIONAL = "National"
    OTHER = "Other"
    SCHOOL = "School"
    SERIES = "Series"
    STATE_LEVEL = "State Level"
    TALUKA = "Taluka"
    VILLAGE = "Village"
    UNIVERSITY = "University"
