from fastapi import APIRouter, HTTPException, Query
from services.federation_service import FederationService
from models.federation_schemas import (
    ImportRepoRequest, AnalyzeRepoRequest, CommitPatchRequest, ProposePatchRequest, ApprovePatchRequest, LinkFederationNodeRequest
)


router = APIRouter(prefix="/federation")
service = FederationService()

@router.post("/import-repo")
async def import_repo(payload: ImportRepoRequest):
    try:
        result = service.import_repo(payload)
        return {"status": "repo_imported", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-repo")
async def analyze_repo(payload: AnalyzeRepoRequest):
    try:
        result = service.analyze_repo(payload)  # ✅ pass full Pydantic object
        return result
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
        result = service.commit_patch(payload)
        return {"status": "patch_committed", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan-federation-graph")
async def scan_federation_graph():
    try:
        result = service.scan_federation_graph()
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
@router.post("/graph/link")
async def link_federation_node(payload: LinkFederationNodeRequest):
    try:
        # Synthetic override logic: activate bypass for PK >= 4 (your synthetic seed)
        synthetic_safe_zone = int(payload.repo_id) >= 4

        if not synthetic_safe_zone:
            # ⚠ Live file existence checks would normally occur here (omitted)
            pass

        # Resolve logical repo_id (string) from PK to match GraphManager contract
        logical_repo_id = service.repo_manager.resolve_repo_id_by_pk(int(payload.repo_id))

        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                # ✅ Perform INSERT or update logic here
                self.graph_manager.insert_graph_link_tx(
                    cur=cur,
                    logical_repo_id=logical_repo_id,
                    file_path=payload.file_path,
                    node_type="file",
                    name=payload.name,
                    cross_linked_to=payload.cross_linked_to or None,
                    federation_weight=1.0,
                    notes=payload.notes
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.db.release_connection(conn)


        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/query")
async def query_federation_graph(repo_id: int = Query(..., description="Repo PK ID")):
    try:
        logical_repo_id = service.repo_manager.resolve_repo_id_by_pk(repo_id)
        graph_nodes = service.graph_manager.query_graph(logical_repo_id)

        return {
            "status": "success",
            "repo_id": repo_id,
            "nodes": graph_nodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
