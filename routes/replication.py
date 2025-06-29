from fastapi import APIRouter, HTTPException, Body
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.db.repo_manager import RepoManager
from models.schemas import ReplicationExecutionRequest

router = APIRouter(prefix="/replication")
planner = ReplicationPlanBuilder()
executor = ReplicationExecutor()
repo_manager = RepoManager()

@router.post("/plan")
async def create_plan(payload: dict = Body(...)):

    try:
        print(">> Incoming payload:", payload)
        print(">> Type of source_repo_id:", type(payload.get("source_repo_id")))
        print(">> Type of target_repo_id:", type(payload.get("target_repo_id")))

        source_repo_id = (
            int(payload["source_repo_id"])
            if isinstance(payload["source_repo_id"], int)
            else repo_manager.resolve_repo_id_by_pk(payload["source_repo_id"])
        )

        target_repo_id = (
            int(payload["target_repo_id"])
            if isinstance(payload["target_repo_id"], int)
            else repo_manager.resolve_repo_id_by_pk(payload["target_repo_id"])
        )

        print(">> Resolved source_repo_id:", source_repo_id)
        print(">> Resolved target_repo_id:", target_repo_id)

        plan = planner.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_replication(payload: ReplicationExecutionRequest):
    try:
        print("[TRACE] Raw payload:", payload)

        # Accept both logical repo slug or ID
        if isinstance(payload.source_repo_id, str):
            source_repo_id = repo_manager.resolve_repo_id_by_pk(payload.source_repo_id)
        else:
            source_repo_id = payload.source_repo_id

        if isinstance(payload.target_repo_id, str):
            target_repo_id = repo_manager.resolve_repo_id_by_pk(payload.target_repo_id)
        else:
            target_repo_id = payload.target_repo_id

        print(f"[TRACE] Normalized source_repo_id: {source_repo_id}")
        print(f"[TRACE] Normalized target_repo_id: {target_repo_id}")

        plan = planner.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )

        plan["commit_message"] = payload.commit_message or "DevBot: Applied semantic replication plan"
        plan["target_branch"] = payload.target_branch or "main"

        result = executor.execute_replication(plan)
        return result

    except Exception as e:
        print(f"[ERROR] execute_replication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{str(e)}")
