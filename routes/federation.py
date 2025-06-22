from fastapi import APIRouter, HTTPException, Query
from services.federation_service import FederationService
from models.federation_schemas import (
    ImportRepoRequest, AnalyzeRepoRequest, CommitPatchRequest, ProposePatchRequest,
    ApprovePatchRequest, LinkFederationNodeRequest, PatchASTProposal, PatchProposalResponse
)

router = APIRouter(prefix="/federation")
service = FederationService()

@router.post("/import-repo")
async def import_repo(payload: ImportRepoRequest):
    try:
        return service.import_repo(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-repo")
async def analyze_repo(payload: AnalyzeRepoRequest):
    try:
        result = service.analyze_repo(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/propose-patch", response_model=PatchProposalResponse)
async def propose_patch(payload: ProposePatchRequest):
    try:
        logical = service.repo_manager.resolve_repo_id_by_pk(int(payload.repo_id))
        owner, repo = logical.split("/")

        patches = []
        for patch in payload.patches:
            composed = service.propose_patch(owner, repo, patch.file_path, payload.branch)
            patches.extend(composed.patches)

        return PatchProposalResponse(patches=patches)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commit-patch")
async def commit_patch(payload: CommitPatchRequest):
    try:
        # Secure patch commit validation
        proposal = service.proposal_manager.get_patch_by_id(payload.proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Patch proposal not found")

        if proposal.status not in ["approved", "manual"]:
            raise HTTPException(status_code=403, detail="Patch not approved")

        if (
            proposal.file_path != payload.file_path or
            proposal.base_sha != payload.base_sha or
            proposal.updated_content.strip() != payload.updated_content.strip()
        ):
            raise HTTPException(status_code=409, detail="Patch payload does not match proposal")

        result = service.commit_patch(proposal)
        service.proposal_manager.update_patch_status(payload.proposal_id, "committed")

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
        logical_repo_id = service.repo_manager.resolve_repo_id_by_pk(payload.repo_id)
        conn = service.db.get_connection()
        try:
            with conn.cursor() as cur:
                service.graph_manager.insert_graph_link_tx(
                    cur,
                    logical_repo_id,
                    payload.file_path,
                    payload.node_type,
                    payload.name,
                    payload.cross_linked_to or "",
                    payload.federation_weight or 1.0,
                    payload.notes or ""
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            service.db.release_connection(conn)

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/query")
async def query_federation_graph(repo_id: int = Query(...)):
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
