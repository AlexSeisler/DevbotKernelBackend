from fastapi import APIRouter, HTTPException, Query, Body
from services.federation_service import FederationService
from models.federation_schemas import ImportRepoRequest, CommitPatchRequest, ProposePatchRequest, ApprovePatchRequest, LinkFederationNodeRequest, PatchASTProposal, PatchProposalResponse
from models.federation_schemas import PatchProposalRequest, PatchProposalResponse
from services.federation_service import execute_patch_proposal
from services.replicator.build_plan import build_replication_plan
from services.replicator.patch_composer import generate_federated_patch
from services.db.proposal_manager import save_patch_proposal
router = APIRouter(prefix='/federation')
service = FederationService()

@router.post('/import-repo')
async def import_repo(payload: ImportRepoRequest):
    try:
        result = service.import_repo(payload)
        return {
            "status": "ok",
            "repo_id": result["repo_id"],
            "files_scanned": result.get("files_scanned", 0),
            "semantic_nodes_extracted": result.get("semantic_nodes_extracted", 0),
            "failed": result.get("failed", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/propose-patch", response_model=PatchProposalResponse)
async def propose_patch(payload: PatchProposalRequest = Body(...)):
    try:
        # 1. Generate the patch using CST Planner
        patch = generate_federated_patch(payload)

        # 2. Save the patch proposal
        save_patch_proposal(
            repo_id=payload.target_repo_id,
            file_path=payload.file_path,
            base_sha=payload.base_sha,
            updated_content=patch["patched_code"],
            diff=patch["diff"],
            metadata=patch["metadata"],
        )

        # 3. Auto-commit patch if valid
        if patch["metadata"].get("change_type") == "insert":
            execute_patch_proposal(
                repo_id=payload.target_repo_id,
                file_path=payload.file_path,
                base_sha=payload.base_sha,
                updated_content=patch["patched_code"],
                commit_message="Auto-committed Federation patch"
            )

        return {
            "status": "success",
            "patched_code": patch["patched_code"],
            "diff": patch["diff"],
            "metadata": patch["metadata"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/commit-patch')
async def commit_patch(payload: CommitPatchRequest):
    try:
        proposal = service.proposal_manager.get_patch_by_id(payload.proposal_id)
        if (not proposal):
            raise HTTPException(status_code=404, detail='Patch proposal not found')
        if (proposal.status not in ['approved', 'manual']):
            raise HTTPException(status_code=403, detail='Patch not approved')
        if ((proposal.file_path != payload.file_path) or (proposal.base_sha != payload.base_sha) or (proposal.updated_content.strip() != payload.updated_content.strip())):
            raise HTTPException(status_code=409, detail='Patch payload does not match proposal')
        result = service.commit_patch(proposal)
        service.proposal_manager.update_patch_status(payload.proposal_id, 'committed')
        return {'status': 'patch_committed', 'data': result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/scan-federation-graph')
async def scan_federation_graph():
    try:
        result = service.scan_federation_graph()
        return {'status': 'graph_scanned', 'data': result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/list-proposals')
async def list_proposals():
    try:
        return service.list_proposals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/approve-patch')
async def approve_patch(payload: ApprovePatchRequest):
    try:
        result = service.approve_patch(payload.proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/reject-patch')
async def reject_patch(payload: ApprovePatchRequest):
    try:
        result = service.reject_patch(payload.proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/graph/link')
async def link_federation_node(payload: LinkFederationNodeRequest):
    from services.db.semantic_manager import SemanticManager
    try:
        if payload.name.strip() == "*":
            default_notes = payload.notes if payload.notes else "autolinked"
            default_node_type = payload.node_type if payload.node_type else "unspecified"
            service.graph_manager.auto_link_all_nodes(
                repo_id=payload.repo_id,
                default_notes=default_notes,
                default_node_type=default_node_type
            )
            return {'status': 'auto_link_complete'}


        logical_repo_id = service.repo_manager.resolve_repo_id_by_pk(payload.repo_id)
        node = SemanticManager().get_node_by_key(payload.repo_id, payload.file_path, payload.name)
        if not node:
            raise HTTPException(status_code=404, detail="Semantic node not found")

        conn = service.db.get_connection()
        try:
            cross_linked_to = payload.dict().get("cross_linked_to", "")
            federation_weight = payload.dict().get("federation_weight", 1.0)
            notes = payload.dict().get("notes", "")
            tags = payload.dict().get("tags", [])

            with conn.cursor() as cur:
                service.graph_manager.insert_graph_link_tx(
                    cur,
                    logical_repo_id,
                    payload.file_path,
                    node.get("node_type", ""),
                    payload.name,
                    cross_linked_to,
                    federation_weight,
                    notes,
                    tags
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            service.db.release_connection(conn)

        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get('/graph/query')
async def query_federation_graph(
    repo_id: int = Query(...),
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0)
):
    try:
        print(f"[DEBUG] Starting federation graph query: repo_id={repo_id}, limit={limit}, offset={offset}")
        
        graph_nodes = service.graph_manager.query_graph(
            repo_id,
            limit=limit,
            offset=offset
        )

        print(f"[DEBUG] Retrieved {len(graph_nodes)} nodes from federation graph")

        has_more = len(graph_nodes) == limit

        return {
            'status': 'success',
            'repo_id': repo_id,
            'nodes': graph_nodes,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': has_more
            }
        }

    except Exception as e:
        print(f"[ERROR] Federation graph query failed: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"Federation graph query failed: {e}")
