from fastapi import APIRouter, HTTPException
from services.db.federation_graph_manager import FederationGraphManager

router = APIRouter(prefix="/federation/graph")
manager = FederationGraphManager()

@router.post("/link")
async def insert_link(payload: dict):
    try:
        manager.insert_graph_link(
            repo_id=payload["repo_id"],
            file_path=payload["file_path"],
            node_type=payload["node_type"],
            name=payload["name"],
            cross_linked_to=payload.get("cross_linked_to", None),
            federation_weight=payload.get("federation_weight", 1.0),
            notes=payload.get("notes", "")
        )
        return {"status": "link_inserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query")
async def query_graph(repo_id: str = None):
    try:
        graph = manager.query_graph(repo_id)
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
