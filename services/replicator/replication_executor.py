from services.replicator.module_extractor import ModuleExtractor
from services.replicator.patch_composer import PatchComposer
from services.federation_service import FederationService
from services.db.repo_manager import RepoManager
from models.federation_schemas import CommitPatchRequest

class ReplicationExecutor:
    def __init__(self):
        self.extractor = ModuleExtractor()
        self.composer = PatchComposer()
        self.federation_service = FederationService()
        self.repo_manager = RepoManager()  # ✅ Needed for repo ID conversion

    def execute_replication(self, plan):
    # Ensure both IDs are logical repo strings
        source_repo = plan["source_repo_id"]
        target_repo = plan["target_repo_id"]
        branch = plan["target_branch"]

        source_owner, source_repo_name = source_repo.split("/")
        target_owner, target_repo_name = target_repo.split("/")

        extraction_results = []
        for module in plan["modules"]:
            extraction_results.append(
                self.extractor.fetch_file_content(source_owner, source_repo_name, module["file_path"], branch)
            )

        patches = self.composer.compose_patch(extraction_results, branch)

        commit_payload = {
            "repo_id": target_repo,
            "branch": branch,
            "commit_message": plan["commit_message"],
            "patches": [
                {
                    **p.dict(),
                    "branch": branch,
                    "commit_message": plan["commit_message"],
                    "repo_id": target_repo
                } for p in patches
            ]
        }

        # ✅ Use commit_patch, which internally manages its own DB connection
        try:
            result = self.federation_service.commit_patch(CommitPatchRequest(**commit_payload))
            return result
        except Exception as e:
            raise Exception(f"Replication failed: {str(e)}")


