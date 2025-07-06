from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from uuid import uuid4

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


class PatchProposalModel(Base):
    __tablename__ = "patch_proposal"

    proposal_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    repo_id = Column(Text)
    branch = Column(Text)
    file_path = Column(Text)
    base_sha = Column(Text)
    anchor = Column(Text)
    code_block = Column(Text)
    patched_code = Column(Text)
    diff = Column(Text)
    patch_metadata = Column("metadata", JSON)
    proposed_by = Column(Text)
    commit_message = Column(Text)
    status = Column(Text, default="pending")
    risk_class = Column(Text)
    diff_summary = Column(Text)
    anchor_lines = Column(JSON, nullable=True)  # ✅ NEW
    created_at = Column(TIMESTAMP, default=datetime.utcnow)