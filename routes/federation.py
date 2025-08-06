from fastapi import APIRouter, HTTPException, Query, Body
from services.federation_service import FederationService
from models.federation_schemas import ProposePatchRequest
from models.federation_schemas import ProposePatchRequest
from services.replicator.federation_patch_planner import FederatedCSTPatchPlanner
from services.github_service import GitHubService  # Ensure this is imported
from services.db.repo_manager import RepoManager
router = APIRouter(prefix='/federation')
service = FederationService()
planner = FederatedCSTPatchPlanner()
github_service = GitHubService()
repo_manager = RepoManager()

@router.post("/propose-patch")
async def propose_patch(request: ProposePatchRequest):
    try:
        proposals = service.handle_propose_patch(request)
        return {"status": "success", "proposals": proposals}
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