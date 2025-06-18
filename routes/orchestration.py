from fastapi import APIRouter, HTTPException
from services.federation_service import FederationService
from services.replicator.replication_plan_builder import ReplicationPlanBuilder
from services.replicator.replication_executor import ReplicationExecutor
from services.github_service import GitHubService
from services.db.repo_manager import RepoManager
from datetime import datetime
from models.federation_schemas import AnalyzeRepoRequest, ReplicateSaaSRequest

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
            conn = self.federation.db.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT name, file_path FROM semantic_node WHERE repo_id = %s", (int(source_repo_id),))
                    nodes = cur.fetchall()
                    for name, file_path in nodes:
                        self.federation.graph_manager.insert_graph_link_tx(
                            cur=cur,
                            logical_repo_id=self.repo_manager.resolve_repo_id_by_pk(source_repo_id),
                            file_path=file_path,
                            node_type="file",
                            name=name,
                            cross_linked_to=None,
                            federation_weight=1.0,
                            notes="Auto-linked by orchestrator"
                        )
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                self.federation.db.release_connection(conn)

            # Step 3: Build replication plan
            print("🧠 Building replication plan...")
            if isinstance(source_repo_id, str):
                raise ValueError("Expected numeric repo_id, got string")
            source_logical = self.repo_manager.resolve_repo_id_by_pk(source_repo_id)
            target_logical = self.repo_manager.resolve_repo_id_by_pk(target_repo_id)
            plan = self.planner.build_plan(source_logical, target_logical)
            plan["commit_message"] = commit_msg
            plan["target_branch"] = branch

            # ✅ Create branch from main
            print("🌿 Creating branch...")
            self.github.create_branch(branch, "main")

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


