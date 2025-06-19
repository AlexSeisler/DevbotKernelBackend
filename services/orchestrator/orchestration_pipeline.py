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
        # ✅ Optional — only needed if testing ingestion again
        # import_payload = ImportRepoRequest(
        #     owner="AlexSeisler",
        #     repo="DevbotKernelBackend",
        #     default_branch="main"
        # )
        # self.federation_service.import_repo(import_payload)

        # ✅ Correctly construct and call semantic analysis
        analyze_payload = AnalyzeRepoRequest(repo_id=source_repo_id)
        self.federation_service.analyze_repo(analyze_payload)

        # ✅ Build full semantic replication plan
        plan = self.plan_builder.build_plan(
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id
        )

        result = self.executor.execute_replication(plan)
        return result
