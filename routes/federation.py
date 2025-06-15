from fastapi import APIRouter, HTTPException
from services.federation_service import FederationService
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest, ProposePatchRequest, CommitPatchRequest

router = APIRouter(prefix="/federation")
federation_service = FederationService()

@router.post("/import-repo")
async def import_repo(payload: ImportRepoRequest):
    try:
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
        result = federation_service.propose_patch(payload)
        return {"status": "patch_proposed", "data": result}
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
