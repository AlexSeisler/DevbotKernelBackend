from fastapi import APIRouter, HTTPException
from services.github_service import GitHubService
from models.schemas import PatchProposal, CommitPatch, PatchProposalCreateRequest  # ✅ Correct class here

router = APIRouter(prefix="/patch")

github_service = GitHubService()

# ✅ PATCH PROPOSAL (Safe Human-in-the-Loop Staging)

@router.post("/proposal")
async def propose_patch(payload: PatchProposalCreateRequest):
    try:
        return {
            "status": "proposal_received",
            "repo_id": payload.repo_id,
            "branch": payload.branch,
            "num_patches": len(payload.patches),
            "sample_patch_preview": payload.patches[0].updated_content[:200] if payload.patches else "No patches"
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
