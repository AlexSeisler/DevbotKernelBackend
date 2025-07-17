from fastapi import APIRouter, HTTPException
from typing import Optional
from services.github_service import GitHubService
from models.schemas import BranchCreateRequest
import urllib.parse

router = APIRouter(prefix="/repo")

# ✅ Load service layer
github_service = GitHubService()

# ✅ Hardcoded owner/repo for now (should be dynamic in future)
OWNER = "AlexSeisler"
REPO = "DevbotKernelBackend"

# ✅ 1️⃣ Hardened Repo Tree Retrieval
@router.get("/tree")
async def get_repo_tree(branch: str = "main", recursive: bool = True):
    try:
        result = github_service.get_repo_tree(OWNER, REPO, branch, recursive)
        return result
    except Exception as e:
        print(f"[ERROR] get_repo_tree failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve repo tree")

# ✅ 2️⃣ Hardened File Content Retrieval
@router.get("/file")
async def get_file_content(
    file_path: str,
    branch: str = "main",
    include_meta: bool = False,
    start_line: int = 1,
    chunk_size: Optional[int] = None
):
    try:
        result = github_service.get_file(
            OWNER,
            REPO,
            file_path,
            branch,
            include_meta=include_meta,
            start_line=start_line,
            chunk_size=chunk_size
        )
        return result
    except Exception as e:
        print(f"[ERROR] get_file_content failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")

# ✅ 3️⃣ Parse structure for a given file
@router.get("/file/structure")
async def parse_file_structure(file_path: str, branch: str = "main"):
    try:
        print(f"[routes/structure] 🔍 Incoming request — file_path={file_path}, branch={branch}")
        return github_service.parse_structure_for_file(OWNER, REPO, file_path, branch, update_cache=True)
    except Exception as e:
        print(f"[routes/structure] ❌ Exception in parse_file_structure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse file structure")


# ✅ 3️⃣ Hardened File History Retrieval
@router.get("/history")
async def get_file_history(file_path: str, branch: str = "main"):
    try:
        result = github_service.get_file_history(OWNER, REPO, file_path, branch)
        return result
    except Exception as e:
        print(f"[ERROR] get_file_history failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file history")

# ✅ 4️⃣ Hardened Branch SHA Retrieval
@router.get("/sha")
async def get_branch_sha(branch: str = "main"):
    try:
        result = github_service.get_branch_sha(OWNER, REPO, branch)
        return result
    except Exception as e:
        print(f"[ERROR] get_branch_sha failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve branch SHA")

# ✅ 5️⃣ Hardened Branch Creation
@router.post("/branch")
async def create_branch(payload: BranchCreateRequest):
    try:
        result = github_service.create_branch(OWNER, REPO, payload.new_branch, payload.base_branch)
        return result
    except Exception as e:
        print(f"[ERROR] create_branch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create branch")
    @router.post("/scaffold/file")
    async def scaffold_file(req: ScaffoldFileRequest):
        try:
            svc = GitHubService()
            return svc.create_file(
                repo_id=req.repo_id,
                branch=req.branch,
                file_path=req.file_path,
                content=req.content,
                commit_message=req.commit_message
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
