from pydantic import BaseModel
from typing import List, Optional

class ImportRepoRequest(BaseModel):
    owner: str
    repo: str
    default_branch: str

class AnalyzeRepoRequest(BaseModel):
    repo_id: int  # 🔧 integer PK now

class PatchObject(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str

class CommitPatchRequest(BaseModel):
    repo_id: str
    branch: str
    file_path: str
    commit_message: str
    base_sha: str
    updated_content: str

class PatchProposal(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str

class ProposePatchRequest(BaseModel):
    repo_id: str
    branch: str
    proposed_by: str
    commit_message: str
    patches: List[PatchProposal]

class ApprovePatchRequest(BaseModel):
    proposal_id: str
class LinkFederationNodeRequest(BaseModel):
    repo_id: int
    file_path: str
    name: str
    cross_linked_to: str = ""
    notes: str
class CommitPatchObject(BaseModel):
    file_path: str
    branch: str
    commit_message: str
    updated_content: str
    base_sha: str
    repo_id: Optional[str] = None  # ✅ Add this field

class ReplicateSaaSRequest(BaseModel):
    source_repo: str
    target_repo: str

class FederationGraphLinkRequest(BaseModel):
    repo_id: int
    file_path: str
    node_type: str
    name: str
    cross_linked_to: Optional[str] = ""
    federation_weight: Optional[float] = 1.0
    notes: Optional[str] = ""
