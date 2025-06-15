from pydantic import BaseModel

class ImportRepoRequest(BaseModel):
    owner: str
    repo: str
    default_branch: str = "main"

class AnalyzeRepoRequest(BaseModel):
    repo_id: str

class ProposePatchRequest(BaseModel):
    repo_id: str
    file_path: str
    patch_summary: str

class CommitPatchRequest(BaseModel):
    repo_id: str
    patch_id: str
