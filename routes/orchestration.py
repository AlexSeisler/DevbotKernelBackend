from fastapi import APIRouter, HTTPException
from services.federation_service import FederationService
from services.db.federation_graph_manager import FederationGraphManager
from services.orchestrator.orchestration_pipeline import OrchestrationPipeline
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.github_service import GitHubService
from services.db.repo_manager import RepoManager
from models.federation_schemas import ReplicateSaaSRequest

router = APIRouter(prefix="/orchestration")

# Service instances
pipeline = OrchestrationPipeline()
repo_manager = RepoManager()

@router.post("/replicate-saas")
async def replicate_saas(payload: ReplicateSaaSRequest):
    try:
        # Resolve logical → physical repo IDs
        source_repo = payload.source_repo
        target_repo = payload.target_repo

        source_pk = repo_manager.resolve_repo_pk(source_repo)
        target_pk = repo_manager.resolve_repo_pk(target_repo)

        # ✅ Use orchestrated pipeline flow
        result = pipeline.run_full_replication(source_pk, target_pk)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full orchestration failed: {str(e)}")
