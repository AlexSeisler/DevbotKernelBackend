from models.core import PatchProposalModel
from sqlalchemy.orm import Session
from datetime import datetime


class ProposalManager:
    def __init__(self, db: Session):
        self.db = db

    def save_proposal(self, proposal: dict):
        """
        Store patch proposal into DB (with LibCST metadata).
        Expects:
            proposal = {
                "file_path": str,
                "base_sha": str,
                "updated_content": str,
                "diff": str,              # NEW
                "metadata": dict,         # NEW
                "repo_id": int,
                "branch": str,
            }
        """
        patch = PatchProposalModel(
            file_path=proposal["file_path"],
            base_sha=proposal["base_sha"],
            updated_content=proposal["updated_content"],
            diff=proposal.get("diff", ""),
            metadata=proposal.get("metadata", {}),
            repo_id=proposal["repo_id"],
            branch=proposal["branch"],
            created_at=datetime.utcnow()
        )
        self.db.add(patch)
        self.db.commit()
        self.db.refresh(patch)
        return patch

    def get_all_proposals(self, repo_id: int):
        return (
            self.db.query(PatchProposalModel)
            .filter(PatchProposalModel.repo_id == repo_id)
            .order_by(PatchProposalModel.created_at.desc())
            .all()
        )
