from fastapi import APIRouter, HTTPException, Query, Body
from services.federation_service import FederationService
from models.federation_schemas import ImportRepoRequest, ProposePatchRequest, LinkFederationNodeRequest
from models.federation_schemas import ProposePatchRequest
from services.replicator.federation_patch_planner import FederatedCSTPatchPlanner
from services.github_service import GitHubService  # Ensure this is imported
from services.db.repo_manager import RepoManager
router = APIRouter(prefix='/federation')
service = FederationService()
planner = FederatedCSTPatchPlanner()
github_service = GitHubService()
repo_manager = RepoManager()

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


@router.post("/propose-patch")
async def propose_patch(request: ProposePatchRequest):
    try:
        proposals = service.handle_propose_patch(request)
        return {"status": "success", "proposals": proposals}
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
