from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FederationRepo(Base):
    __tablename__ = 'federation_repo'

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, unique=True)  # Ensure INTEGER type
    branch = Column(String)
    root_sha = Column(String)

