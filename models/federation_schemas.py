from pydantic import BaseModel
from typing import List

# Federation ingestion request payload
class ImportRepoRequest(BaseModel):
    owner: str
    repo: str
    default_branch: str

# Analyzer uses internal PK reference
class AnalyzeRepoRequest(BaseModel):
    repo_id: int

# Unified patch object for both propose/commit
class PatchObject(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str

class CommitPatchRequest(BaseModel):
    repo_id: int  # corrected to integer PK
    branch: str
    commit_message: str
    patches: List[PatchObject]

class ProposePatchRequest(BaseModel):
    repo_id: int  # corrected to integer PK
    branch: str
    commit_message: str
    proposed_by: str
    patches: List[PatchObject]

class ApprovePatchRequest(BaseModel):
    proposal_id: int  # safe to make integer here for consistency
