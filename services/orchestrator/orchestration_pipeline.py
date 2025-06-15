from services.federation_service import FederationService
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor

class OrchestrationPipeline:
    def __init__(self):
        self.federation_service = FederationService()
        self.plan_builder = ReplicationPlanBuilder()
        self.executor = ReplicationExecutor()

    def run_full_replication(self, source_repo, target_repo):
        owner, repo = source_repo.split("/")
        self.federation_service.import_repo({
            "owner": owner,
            "repo": repo,
            "default_branch": "main"
        })

        self.federation_service.analyze_repo({
            "repo_id": source_repo
        })

        # Federation Graph population would normally occur here via GPT agent

        plan = self.plan_builder.build_plan(
            source_repo_id=source_repo,
            target_repo_id=target_repo
        )

        result = self.executor.execute_replication(plan)
        return result
