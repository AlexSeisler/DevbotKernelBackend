from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# ✅ Branch Creation Schema
class BranchCreateRequest(BaseModel):
    new_branch: str = Field(..., description="The name of the branch to create")
    base_branch: str = Field("main", description="The base branch to create from")

# ✅ Patch Proposal Schema
class PatchProposal(BaseModel):
    file_path: str = Field(..., description="Path of file to patch")
    base_sha: str = Field(..., description="SHA of the base commit or file version")
    updated_content: str = Field(..., description="New content for the file")

# ✅ Patch Commit Schema
class PatchCommit(BaseModel):
    file_path: str = Field(..., description="File path to commit")
    commit_message: str = Field(..., description="Commit message for patch")
    updated_content: str = Field(..., description="Updated file content (raw string)")
    branch: str = Field("main", description="Branch to commit on")

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
    source_branch: str = Field(..., description="The branch containing changes (head)")
    target_branch: str = Field(..., description="The branch to merge into (base)")
    title: str = Field(..., description="Title for the pull request")
    body: str = Field(..., description="Description of pull request")
