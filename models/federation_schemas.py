from pydantic import BaseModel
from typing import List

class ImportRepoRequest(BaseModel):
    owner: str
    repo: str
    default_branch: str = "main"

class AnalyzeRepoRequest(BaseModel):
    repo_id: str

class PatchObject(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str

class CommitPatchRequest(BaseModel):
    repo_id: str
    branch: str
    commit_message: str
    patches: List[PatchObject]

class ProposePatchRequest(BaseModel):
    repo_id: str
    branch: str
    commit_message: str
    proposed_by: str
    patches: List[PatchObject]

class ApprovePatchRequest(BaseModel):
    proposal_id: str
