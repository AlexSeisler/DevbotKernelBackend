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
