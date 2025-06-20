from services.federation_service import FederationService
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from models.federation_schemas import AnalyzeRepoRequest, ImportRepoRequest

class OrchestrationPipeline:
    def __init__(self):
        self.federation_service = FederationService()
        self.plan_builder = ReplicationPlanBuilder()
        self.executor = ReplicationExecutor()

    def run_full_replication(self, source_repo_id: int, target_repo_id: int):
        try:
            analyze_payload = AnalyzeRepoRequest(repo_id=source_repo_id)
            self.federation_service.analyze_repo(analyze_payload)

            plan = self.plan_builder.build_plan(
                source_repo_id=source_repo_id,
                target_repo_id=target_repo_id
            )

            result = self.executor.execute_replication(plan)
            return result

        except Exception as e:
            return {"error": "Full orchestration failed", "detail": str(e)}