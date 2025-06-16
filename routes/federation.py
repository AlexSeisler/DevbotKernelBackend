from fastapi import APIRouter, HTTPException, Request
from models.federation_schemas import (
    ImportRepoRequest, AnalyzeRepoRequest, CommitPatchRequest, ProposePatchRequest, ApprovePatchRequest
)

router = APIRouter(prefix="/federation")

@router.post("/import-repo")
async def import_repo(payload: ImportRepoRequest, request: Request):
    try:
        federation_service = request.app.federation_service
        result = federation_service.import_repo(payload)
        return {"status": "repo_imported", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-repo")
async def analyze_repo(payload: AnalyzeRepoRequest):
    try:
        result = federation_service.analyze_repo(payload)
        return {"status": "repo_analyzed", "data": result}
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
