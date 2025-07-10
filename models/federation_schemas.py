from pydantic import BaseModel, Field
from typing import List, Optional, Tuple


class ImportRepoRequest(BaseModel):
    owner: str
    repo: str
    default_branch: str


class PatchObject(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str
    risk_score: Optional[float] = 0.0  # Existing field
    risk_class: Optional[str] = "UNKNOWN"  # Phase 2: Risk classification
    diff_summary: Optional[str] = None  # 🧠 Phase 3


class CommitPatchRequest(BaseModel):
    proposal_id: str
    file_path: str
    base_sha: str
    updated_content: str


class PatchProposal(BaseModel):
    file_path: str
    base_sha: str
    anchor: str
    code_block: str
    anchor_lines: Optional[List[int]] = None
    anchor_path: Optional[List[str]] = None  # ✅ hierarchical path to anchor
    patch_strategy: Optional[str] = "insert"  # ✅ NEW: mutation mode (insert, append, replace, delete)



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
    node_type: str
    federation_weight: Optional[float] = 1.0
    tags: Optional[List[str]] = []  # 🧠 NEW FIELD


class CommitPatchObject(BaseModel):
    file_path: str
    branch: str
    commit_message: str
    updated_content: str
    base_sha: str
    repo_id: Optional[str] = None  # 🧠 Add this field


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


class PatchASTProposal(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str

    # Phase 3 risk classification + audit fields
    risk_score: Optional[float] = 0.0  # Future use: automated score
    risk_class: Optional[str] = "UNKNOWN"  # Must be explicitly set at save time
    diff_summary: Optional[str] = None  # Summarized diff changes (e.g., "added def foo")
    manual: bool = Field(default=True)
    diff: Optional[str] = None  # 🧠 NEW: Full diff
    metadata: Optional[dict] = None  # 🧠 NEW: CST patch details


class PatchProposalResponse(BaseModel):
    patches: List[PatchASTProposal]


class SemanticNode(BaseModel):
    node_type: str  # 'function' or 'class'
    name: str
    args: Optional[List[str]] = []
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    decorators: Optional[List[str]] = []
    inherits_from: Optional[List[str]] = []
    code_block: Optional[str] = None
    interface_type: Optional[str] = None
    methods: Optional[List[str]] = []  # for class nodes
    file_path: str
    line_range: Optional[Tuple[int, int]] = None
    uuid: str
    tags: Optional[List[str]] = []
