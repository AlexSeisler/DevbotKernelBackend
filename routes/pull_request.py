from fastapi import APIRouter, HTTPException
from services.github_service import GitHubService
from models.schemas import PullRequestCreateRequest

router = APIRouter(prefix="/repo")

github_service = GitHubService()

# ✅ GPT-controlled Pull Request Creation
@router.post("/pull-request")
async def create_pull_request(payload: PullRequestCreateRequest):
    try:
        result = github_service.create_pull_request(
            source_branch=payload.source_branch,
            target_branch=payload.target_branch,
            title=payload.title,
            body=payload.body
        )
        return {
            "status": "pull_request_created",
            "pr_url": result.get("html_url"),
            "pr_number": result.get("number"),
            "merged": result.get("merged", False)
        }
    except Exception as e:
        print(f"[ERROR] create_pull_request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create pull request")
