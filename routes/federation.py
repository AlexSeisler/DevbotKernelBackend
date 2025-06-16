from fastapi import APIRouter, HTTPException, Request
from services.federation_service import FederationService
from models.federation_schemas import (
    ImportRepoRequest, AnalyzeRepoRequest, CommitPatchRequest, ProposePatchRequest, ApprovePatchRequest
)

router = APIRouter(prefix="/federation")
service = FederationService()
@router.post("/import-repo")
async def import_repo(payload: ImportRepoRequest, request: Request):
    try:
        federation_service = request.app.federation_service
        result = federation_service.import_repo(payload)
        return {"status": "repo_imported", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def analyze_repo(self, payload: AnalyzeRepoRequest):
    try:
        repo_metadata = self.github_service.get_repo_metadata(payload.owner, payload.repo)
        branch = payload.branch or repo_metadata.get("default_branch", "main")
        repo_tree = self.github_service.get_repo_tree(payload.owner, payload.repo, branch)
        analysis_result = self.analyze_repo_tree(repo_tree)
        return analysis_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/propose-patch")
async def propose_patch(payload: ProposePatchRequest):
    try:
        result = service.propose_patch(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commit-patch")
async def commit_patch(payload: CommitPatchRequest):
    try:
        result = federation_service.commit_patch(payload)
        return {"status": "patch_committed", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan-federation-graph")
async def scan_federation_graph():
    try:
        result = federation_service.scan_federation_graph()
        return {"status": "graph_scanned", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/list-proposals")
async def list_proposals():
    try:
        return service.list_proposals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/approve-patch")
async def approve_patch(payload: ApprovePatchRequest):
    try:
        result = service.approve_patch(payload.proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/reject-patch")
async def reject_patch(payload: ApprovePatchRequest):
    try:
        result = service.reject_patch(payload.proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
