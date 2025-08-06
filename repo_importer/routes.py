from fastapi import APIRouter, HTTPException
from models.federation_schemas import ImportRepoRequest
from repo_importer.importer import RepoIngestion
from models.federation_schemas import LinkFederationNodeRequest
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from settings import _db_instance
import logging
import os

router = APIRouter(prefix='/repo-ingestion')

service = RepoIngestion()
repo_manager = RepoManager()
graph_manager = FederationGraphManager()
database = _db_instance
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

@router.post('/graph/link')
async def link_federation_node(payload: LinkFederationNodeRequest):
    from services.db.semantic_manager import SemanticManager
    try:
        if payload.name.strip() == "*":
            default_notes = payload.notes if payload.notes else "autolinked"
            default_node_type = payload.node_type if payload.node_type else "unspecified"
            graph_manager.auto_link_all_nodes(
                repo_id=payload.repo_id,
                default_notes=default_notes,
                default_node_type=default_node_type
            )
            return {'status': 'auto_link_complete'}


        logical_repo_id = service.repo_manager.resolve_repo_id_by_pk(payload.repo_id)
        node = SemanticManager().get_node_by_key(payload.repo_id, payload.file_path, payload.name)
        if not node:
            raise HTTPException(status_code=404, detail="Semantic node not found")

        conn = database.get_connection()
        try:
            cross_linked_to = payload.dict().get("cross_linked_to", "")
            federation_weight = payload.dict().get("federation_weight", 1.0)
            notes = payload.dict().get("notes", "")
            tags = payload.dict().get("tags", [])

            with conn.cursor() as cur:
                graph_manager.insert_graph_link_tx(
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
            database.release_connection(conn)

        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
