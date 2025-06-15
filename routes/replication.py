from fastapi import APIRouter, HTTPException
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor

router = APIRouter(prefix="/replication")
planner = ReplicationPlanBuilder()
executor = ReplicationExecutor()

@router.post("/plan")
async def create_plan(payload: dict):
    try:
        plan = planner.build_plan(
            source_repo_id=payload["source_repo_id"],
            target_repo_id=payload["target_repo_id"]
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_replication(payload: dict):
    try:
        result = executor.execute_replication(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
