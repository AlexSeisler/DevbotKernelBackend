from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FederationRepo(Base):
    __tablename__ = 'federation_repo'

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, unique=True)
    owner = Column(String)  # ✅ Needed for commit
    repo = Column(String)   # ✅ Needed for commit
    branch = Column(String)
    root_sha = Column(String)

