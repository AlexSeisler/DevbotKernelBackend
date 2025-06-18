from fastapi import APIRouter, HTTPException
from services.federation_service import FederationService
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.github_service import GitHubService
from services.db.repo_manager import RepoManager
from datetime import datetime
from models.federation_schemas import AnalyzeRepoRequest

router = APIRouter(prefix="/orchestrate")  # ✅ Main router for orchestration endpoints


# ✅ Stage 17 Ready: Full pipeline with live branch creation
class OrchestrationPipeline:
    def __init__(self):
        self.federation = FederationService()
        self.planner = ReplicationPlanBuilder()
        self.executor = ReplicationExecutor()
        self.github = GitHubService()
        self.repo_manager = RepoManager()

    def run_full_replication(self, source_repo_id, target_repo_id):
        try:
            # ✅ Auto-generate branch to avoid duplicate PR issues
            branch = f"devbot-replication-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            commit_msg = "DevBot: Full SaaS replication test"

            # Step 1: Analyze repo
            print("🔍 Analyzing repo...")
            self.federation.analyze_repo(AnalyzeRepoRequest(repo_id=source_repo_id))

            # Step 2: Link semantic nodes into federation graph
            print("🔗 Linking semantic nodes...")
            with self.federation.db.cursor() as cur:
                cur.execute("SELECT name, file_path FROM semantic_node WHERE repo_id = %s", (source_repo_id,))
                nodes = cur.fetchall()
                for name, file_path in nodes:
                    self.federation.graph_manager.insert_graph_link_tx(
                        cur,
                        self.repo_manager.resolve_repo_id_by_pk(source_repo_id),
                        file_path,
                        "file",
                        name,
                        None,
                        1.0,
                        "Auto-linked by orchestrator"
                    )
            self.federation.db.commit()

            # Step 3: Build replication plan
            print("🧠 Building replication plan...")
            source_logical = self.repo_manager.resolve_repo_id_by_pk(source_repo_id)
            target_logical = self.repo_manager.resolve_repo_id_by_pk(target_repo_id)
            plan = self.planner.build_plan(source_logical, target_logical)
            plan["commit_message"] = commit_msg
            plan["target_branch"] = branch

            # ✅ Create branch from main
            print("🌿 Creating branch...")
            default_sha = self.github.get_branch_sha("main")["object"]["sha"]
            self.github.create_branch(branch, default_sha)

            # Step 4: Execute semantic patch commit
            print("🚀 Executing patch commit...")
            result = self.executor.execute_replication(plan)

            # Step 5: Open pull request
            print("📬 Creating pull request...")
            pr = self.github.create_pull_request(
                owner=source_logical.split("/")[0],
                repo=source_logical.split("/")[1],
                source_branch=branch,
                target_branch="main",
                title="DevBot Final Validation PR",
                body="Full DevBot Orchestration validation sequence"
            )

            return {
                "status": "orchestration_complete",
                "replication_result": result,
                "pull_request_url": pr.get("html_url")
            }

        except Exception as e:
            raise Exception(f"Full orchestration failed: {str(e)}")


# ✅ Mounted orchestrator endpoint
pipeline = OrchestrationPipeline()

@router.post("/replicate-saas")
async def replicate_saas(payload: dict):
    try:
        source_repo = payload["source_repo"]
        target_repo = payload["target_repo"]
        result = pipeline.run_full_replication(source_repo, target_repo)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
