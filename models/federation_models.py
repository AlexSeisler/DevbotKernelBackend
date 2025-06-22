from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FederationRepo(Base):
    __tablename__ = 'federation_repo'

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, unique=True)         # GitHub numeric ID
    logical_repo_id = Column(String, unique=True)  # e.g., "AlexSeisler/DevbotKernelBackend"
    owner = Column(String)
    repo = Column(String)
    branch = Column(String)
    root_sha = Column(String)
    risk_class = Column(String, nullable=True)  
    diff_summary = Column(String, nullable=True)   # ✅ Added for AST Phase 2
