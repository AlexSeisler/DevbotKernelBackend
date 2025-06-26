from fastapi import APIRouter, HTTPException
from datetime import datetime

# Core services
from services.federation_service import FederationService
from services.db.federation_graph_manager import FederationGraphManager
from services.orchestrator.orchestration_pipeline import OrchestrationPipeline

# Replication pipeline modules
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.github_service import GitHubService
from services.db.repo_manager import RepoManager

# Data models
from models.federation_schemas import AnalyzeRepoRequest, ReplicateSaaSRequest

# FastAPI router
router = APIRouter(prefix="/orchestrate")

# Federation and replication service instances
federation = FederationService()
graph_manager = FederationGraphManager()
pipeline = OrchestrationPipeline()


# Orchestration pipeline class
class OrchestrationPipeline:
    def __init__(self):
        self.federation = FederationService()
        self.planner = ReplicationPlanBuilder()
        self.executor = ReplicationExecutor()
        self.github = GitHubService()
        self.repo_manager = RepoManager()



@router.post("/replicate-saas")
async def run_full_replication(source_repo_id: str, target_repo_id: str):
    try:
        # Step 1: Resolve repo IDs
        source_pk = federation.repo_manager.resolve_repo_pk(source_repo_id)
        target_pk = federation.repo_manager.resolve_repo_pk(target_repo_id)

        # Step 2: Skip analysis for zip-based repos (already parsed)
        if not source_repo_id.startswith("zip-"):
            federation.analyze_repo({"repo_id": source_repo_id})

        # Step 3: Load semantic nodes in paginated chunks
        all_nodes = []
        offset = 0
        limit = 100
        while True:
            chunk = graph_manager.query_graph(source_repo_id, limit=limit, offset=offset)
            all_nodes.extend(chunk)
            if len(chunk) < limit:
                break
            offset += limit

        if not all_nodes:
            raise HTTPException(status_code=404, detail="No semantic nodes found.")

        # Step 4: Build and execute patch plan in safe batches
        patch_batch = []
        MAX_BATCH = 10
        applied = []
        for node in all_nodes:
            plan = replicator.generate_patch_from_node(node, target_repo_id)
            if plan:
                patch_batch.append(plan)

            if len(patch_batch) >= MAX_BATCH:
                try:
                    replicator.apply_patch_batch(patch_batch, target_repo_id)
                    applied.extend(patch_batch)
                except Exception as e:
                    print(f"[BATCH ERROR] {str(e)}")
                patch_batch = []

        # Final leftovers
        if patch_batch:
            replicator.apply_patch_batch(patch_batch, target_repo_id)
            applied.extend(patch_batch)

        return {
            "source_repo_id": source_repo_id,
            "target_repo_id": target_repo_id,
            "patches_applied": len(applied),
            "status": "replication_complete"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replication failed: {str(e)}")




# ✅ Mounted orchestrator endpoint
pipeline = OrchestrationPipeline()
repo_manager = RepoManager()

@router.post("/replicate-saas")
async def replicate_saas(payload: ReplicateSaaSRequest):
    try:
        # ✅ Corrected attribute access
        source_repo = payload.source_repo
        target_repo = payload.target_repo

        source_pk = repo_manager.resolve_repo_pk(source_repo)
        target_pk = repo_manager.resolve_repo_pk(target_repo)

        result = pipeline.run_full_replication(source_pk, target_pk)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full orchestration failed: {str(e)}")


