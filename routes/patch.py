from fastapi import APIRouter, HTTPException
from services.github_service import GitHubService
from models.schemas import PatchProposal, CommitPatch  # ✅ Correct class here

router = APIRouter(prefix="/patch")

github_service = GitHubService()

# ✅ PATCH PROPOSAL (Safe Human-in-the-Loop Staging)
@router.post("/proposal")
async def propose_patch(payload: PatchProposal):
    try:
        return {
            "status": "proposal_received",
            "file_path": payload.file_path,
            "base_sha": payload.base_sha,
            "preview_content_sample": payload.updated_content[:250]
        }
    except Exception as e:
        print(f"[ERROR] propose_patch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register patch proposal")

# ✅ PATCH COMMIT (GPT-controlled Safe Commit Execution)
@router.post("/commit")
async def commit_patch(payload: CommitPatch):
    try:
        result = github_service.commit_patch(payload)
        commit_sha = result.get("commit", {}).get("sha", None)
        content_path = result.get("content", {}).get("path", None)

        return {
            "status": "patch_committed",
            "commit_sha": commit_sha,
            "content_path": content_path
        }
    except Exception as e:
        print(f"[ERROR] commit_patch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to commit patch safely")
