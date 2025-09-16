from fastapi import APIRouter, HTTPException
from typing import Optional
from services.github_service import GitHubService
from models.schemas import BranchCreateRequest
from models.federation_schemas import ScaffoldFileRequest
import urllib.parse

router = APIRouter(prefix="/repo")

# ✅ Load service layer
github_service = GitHubService()

def parse_repo_id(repo_id: str):
    try:
        owner, repo = repo_id.split("/")
        return owner, repo
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo_id format. Use 'owner/repo'.")

# ✅ 1️⃣ Repo Tree Retrieval with dynamic repo_id
@router.get("/tree")
async def get_repo_tree(
    repo_id: str,
    branch: str = "main",
    recursive: bool = True,
    path_prefix: Optional[str] = "",
    limit: int = 500,
    offset: int = 0
):
    """
    Repo Tree Retrieval (safe + paginated)
    - Supports limit & offset for pagination
    - Gracefully handles oversized trees
    """
    try:
        owner, repo = parse_repo_id(repo_id)
        result = github_service.get_repo_tree(
            owner,
            repo,
            branch,
            recursive,
            limit=limit,
            offset=offset,
            path_prefix=path_prefix
        )
        return result
    except Exception as e:
        print(f"[ERROR] get_repo_tree failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve repo tree")

# ✅ 2️⃣ File Content Retrieval with dynamic repo_id
@router.get("/file")
async def get_file_content(
    repo_id: str,
    file_path: str,
    branch: str = "main",
    include_meta: bool = False,
    start_line: int = 1,
    chunk_size: Optional[int] = None
):
    try:
        owner, repo = parse_repo_id(repo_id)
        result = github_service.get_file(
            owner,
            repo,
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

# ✅ 3️⃣ File Structure Parsing
@router.get("/file/structure")
async def parse_file_structure(repo_id: str, file_path: str, branch: str = "main"):
    try:
        owner, repo = parse_repo_id(repo_id)
        return github_service.parse_structure_for_file(owner, repo, file_path, branch, update_cache=True)
    except Exception as e:
        print(f"[ERROR] parse_file_structure failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse file structure")

# ✅ 4️⃣ File History Retrieval
@router.get("/history")
async def get_file_history(repo_id: str, file_path: str, branch: str = "main"):
    try:
        owner, repo = parse_repo_id(repo_id)
        return github_service.get_file_history(owner, repo, file_path, branch)
    except Exception as e:
        print(f"[ERROR] get_file_history failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file history")

# ✅ 5️⃣ Branch SHA Retrieval
@router.get("/sha")
async def get_branch_sha(repo_id: str, branch: str = "main"):
    try:
        owner, repo = parse_repo_id(repo_id)
        return github_service.get_branch_sha(owner, repo, branch)
    except Exception as e:
        print(f"[ERROR] get_branch_sha failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve branch SHA")

# ✅ 6️⃣ Branch Creation
@router.post("/branch")
async def create_branch(payload: BranchCreateRequest):
    try:
        owner, repo = parse_repo_id(payload.repo_id)
        return github_service.create_branch(owner, repo, payload.new_branch, payload.base_branch)
    except Exception as e:
        print(f"[ERROR] create_branch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create branch")

# ✅ 7️⃣ File Scaffold Creation (already supports repo_id)
@router.post("/scaffold/file")
async def scaffold_file(req: ScaffoldFileRequest):
    try:
        return github_service.create_file(
            repo_id=req.repo_id,
            branch=req.branch,
            file_path=req.file_path,
            content=req.content,
            commit_message=req.commit_message
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
