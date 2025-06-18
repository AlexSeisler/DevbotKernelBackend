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
async def execute_replication(payload: ReplicationExecutionRequest):
    try:
        print("[DEBUG] Raw payload:", payload)

        # Directly access attributes of the Pydantic model
        source_repo_pk = payload.source_repo_id
        target_repo_pk = payload.target_repo_id

        if not source_repo_pk or not target_repo_pk:
            raise ValueError("Missing source_repo_id or target_repo_id")

        # Normalize repo PKs to logical string IDs
        source_repo_id = repo_manager.resolve_repo_id_by_pk(source_repo_pk)
        target_repo_id = repo_manager.resolve_repo_id_by_pk(target_repo_pk)

        print("[DEBUG] Resolved Source:", source_repo_id)
        print("[DEBUG] Resolved Target:", target_repo_id)

        # Build plan
        plan = planner.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )

        print("[DEBUG] Plan:", plan)

        # Inject commit metadata
        plan["commit_message"] = payload.commit_message or "DevBot: Apply semantic replication plan"
        plan["target_branch"] = payload.target_branch or "main"

        # Execute
        result = executor.execute_replication(plan)
        return result

    except Exception as e:
        print(f"[ERROR] execute_replication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{str(e)}")
