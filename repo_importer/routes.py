from fastapi import APIRouter, HTTPException
from models.federation_schemas import ImportRepoRequest
from repo_importer.importer import RepoIngestion
from models.federation_schemas import LinkFederationNodeRequest
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from repo_importer.node_retrieval import fetch_nodes_by_subsystem
from models.query_schema import ProjectTaskQueue
from services.db.project_task_queue_manager import insert_project_task, get_project_tasks
from settings import _db_instance
import logging
import os
from typing import Optional

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
@router.get('/nodes')
async def get_nodes(repo_id: str, subsystem: Optional[str] = None, fields: Optional[str] = None):
    if fields == "slim":
        columns = ["file_path", "name", "node_type"]
    elif fields == "slim-code":
        columns = ["file_path", "name", "node_type", "code_block"]
    else:
        columns = None  # full node
    return fetch_nodes_by_subsystem(repo_id, subsystem, columns)


@router.get('/node-summary')
async def get_node_summary(repo_id: str):
    from repo_importer.node_retrieval import generate_node_summary
    return generate_node_summary(repo_id)
@router.post('/project-task-queue/insert')
async def insert_project_task_queue(payload: ProjectTaskQueue):
    try:
        inserted = insert_project_task(payload.dict())
        return {"status": "ok", "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/project-task-queue')
async def get_project_task_queue(
    repo_id: Optional[str] = None,
    phase: Optional[str] = None,
    subsystem: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = 100
):
    filters = {}
    if repo_id:
        filters["repo_id"] = repo_id
    if phase:
        filters["phase"] = phase
    if subsystem:
        filters["subsystem"] = [subsystem]
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority

    try:
        tasks = get_project_tasks(filters=filters, limit=limit)
        return {"status": "ok", "tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))