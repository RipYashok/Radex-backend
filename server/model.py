from sqlalchemy import Column, Integer, String
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String, nullable=False)
    status = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    images = Column(JSON, nullable=True)
    reports = Column(JSON, nullable=True)