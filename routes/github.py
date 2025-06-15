from fastapi import APIRouter, HTTPException
from services.github_service import GitHubService
from models.schemas import BranchCreateRequest
import urllib.parse

router = APIRouter(prefix="/repo")

# ✅ Load service layer
github_service = GitHubService()

# ✅ 1️⃣ Hardened Repo Tree Retrieval
@router.get("/tree")
async def get_repo_tree(branch: str = "main", recursive: bool = True):
    try:
        result = github_service.get_repo_tree(branch, recursive)
        return result
    except Exception as e:
        print(f"[ERROR] get_repo_tree failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve repo tree")

# ✅ 2️⃣ Hardened File Content Retrieval
@router.get("/file")
async def get_file_content(file_path: str, branch: str = "main"):
    try:
        encoded_path = urllib.parse.quote(file_path, safe="")
        result = github_service.get_file(file_path, branch)
        return result
    except Exception as e:
        print(f"[ERROR] get_file_content failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")

# ✅ 3️⃣ Hardened File History Retrieval
@router.get("/history")
async def get_file_history(file_path: str, branch: str = "main"):
    try:
        result = github_service.get_file_history(file_path, branch)
        return result
    except Exception as e:
        print(f"[ERROR] get_file_history failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file history")

# ✅ 4️⃣ Hardened Branch SHA Retrieval
@router.get("/sha")
async def get_branch_sha(branch: str = "main"):
    try:
        result = github_service.get_branch_sha(branch)
        return result
    except Exception as e:
        print(f"[ERROR] get_branch_sha failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve branch SHA")

# ✅ 5️⃣ Hardened Branch Creation
@router.post("/branch")
async def create_branch(payload: BranchCreateRequest):
    try:
        result = github_service.create_branch(payload.new_branch, payload.base_branch)
        return result
    except Exception as e:
        print(f"[ERROR] create_branch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create branch")
