from models.federation_models import PatchProposalModel
from db.session import SessionLocal
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

def save_patch_proposal(payload: Dict[str, Any]):
    """
    Accepts a structured ProposePatchRequest payload and saves each patch into the DB.
    Payload shape:
    {
        "repo_id": "string",
        "branch": "string",
        "proposed_by": "string",
        "commit_message": "string",
        "patches": [
            {
                "file_path": "string",
                "base_sha": "string",
                "anchor": "string",
                "code_block": "string"
            }
        ]
    }
    """
    db: Session = SessionLocal()

    try:
        for patch in payload.get("patches", []):
            proposal = PatchProposalModel(
                repo_id=payload["repo_id"],
                branch=payload["branch"],
                file_path=patch["file_path"],
                base_sha=patch["base_sha"],
                proposed_by=payload.get("proposed_by", "devbot"),
                commit_message=payload.get("commit_message", "Federated patch proposal"),
                anchor=patch.get("anchor"),
                updated_content=patch["code_block"],
                patch_id=str(uuid.uuid4())
            )
            db.add(proposal)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    def get_all_proposals(self, repo_id: int):
        return (
            self.db.query(PatchProposalModel)
            .filter(PatchProposalModel.repo_id == repo_id)
            .order_by(PatchProposalModel.created_at.desc())
            .all()
        )
