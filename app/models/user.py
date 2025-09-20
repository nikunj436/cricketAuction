from sqlalchemy import Column, Integer, String, Enum
from app.db.base import Base
from app.enums.role import Role

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, unique=True, index=True, nullable=True) # <--- Add this line
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.USER, nullable=False)