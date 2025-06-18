from fastapi import APIRouter, HTTPException
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.db.repo_manager import RepoManager

router = APIRouter(prefix="/replication")
planner = ReplicationPlanBuilder()
executor = ReplicationExecutor()
repo_manager = RepoManager()

@router.post("/plan")
async def create_plan(payload: dict):
    try:
        source_repo_id = repo_manager.resolve_repo_id_by_pk(payload["source_repo_id"])
        target_repo_id = repo_manager.resolve_repo_id_by_pk(payload["target_repo_id"])

        plan = planner.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_replication(payload: dict):
    try:
        # 🔧 Normalize repo_id to logical form before execution
        source_repo_id = repo_manager.resolve_repo_id_by_pk(payload["source_repo_id"])
        target_repo_id = repo_manager.resolve_repo_id_by_pk(payload["target_repo_id"])

        plan = planner.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )
        plan["commit_message"] = payload["commit_message"]
        plan["target_branch"] = payload["target_branch"]

        result = executor.execute_replication(plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
