from fastapi import APIRouter, HTTPException
from services.github_service import GitHubService
from services.db.repo_manager import RepoManager
from models.schemas import PullRequestCreateRequest

router = APIRouter(prefix="/repo")

github_service = GitHubService()
repo_manager = RepoManager()

# ✅ GPT-controlled Pull Request Creation with resolved repo_id
@router.post("/pull-request")
async def create_pull_request(payload: PullRequestCreateRequest):
    try:
        # 🔐 Use known repo_id 4 → AlexSeisler/DevbotKernelBackend
        logical_repo_id = repo_manager.resolve_repo_id_by_pk(4)
        owner, repo = logical_repo_id.split("/")

        result = github_service.create_pull_request(
            owner=owner,
            repo=repo,
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
        raise HTTPException(status_code=500, detail=str(e))

