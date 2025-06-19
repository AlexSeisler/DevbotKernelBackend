from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# ✅ Branch Creation Schema
class BranchCreateRequest(BaseModel):
    new_branch: str = Field(..., description="The name of the branch to create")
    base_branch: str = Field("main", description="The base branch to create from")

# ✅ File Deletion Schema
class DeleteFileRequest(BaseModel):
    file_path: str = Field(..., description="Path of file to delete")
    commit_message: str = Field(..., description="Commit message for file deletion")
    sha: str = Field(..., description="SHA of file to delete")
    branch: str = Field("main", description="Branch to delete from")

# ✅ Multi-file Federation Commit Schema
class MultiFileCommitRequest(BaseModel):
    message: str = Field(..., description="Commit message for multi-file commit")
    files: List[Dict[str, str]] = Field(..., description="List of file dicts with 'path' and 'content'")
    branch: str = Field("main", description="Branch to commit into")

# ✅ Pull Request Schema
class PullRequestCreateRequest(BaseModel):
    source_branch: str
    target_branch: str
    title: str
    body: str

class ReplicationExecutionRequest(BaseModel):
    source_repo_id: int
    target_repo_id: int
    commit_message: str
    target_branch: str
    