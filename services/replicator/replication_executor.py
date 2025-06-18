from services.replicator.module_extractor import ModuleExtractor
from services.replicator.patch_composer import PatchComposer
from services.federation_service import FederationService

class ReplicationExecutor:
    def __init__(self):
        self.extractor = ModuleExtractor()
        self.composer = PatchComposer()
        self.federation_service = FederationService()

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
            "repo_id": target_repo,  # logical string form
            "branch": branch,
            "commit_message": plan["commit_message"],
            "patches": [p.dict() for p in patches]
        }

        # ✅ Hardened transaction safety around commit logic
        try:
            with self.federation_service.db:
                with self.federation_service.db.cursor() as cur:
                    # If commit_patch writes to DB in future, this ensures safety
                    return self.federation_service.commit_patch(commit_payload)
        except Exception as e:
            self.federation_service.db.rollback()
            raise Exception(f"Replication failed: {str(e)}")
