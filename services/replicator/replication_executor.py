from services.replicator.module_extractor import ModuleExtractor
from services.replicator.patch_composer import PatchComposer
from services.federation_service import FederationService

class ReplicationExecutor:
    def __init__(self):
        self.extractor = ModuleExtractor()
        self.composer = PatchComposer()
        self.federation_service = FederationService()

    def execute_replication(self, plan):
        source_owner, source_repo = plan["source_repo_id"].split("/")
        target_owner, target_repo = plan["target_repo_id"].split("/")
        branch = "main"

        extraction_results = []
        for module in plan["modules"]:
            file_path = module["file_path"]
            extraction_results.append(
                self.extractor.fetch_file_content(source_owner, source_repo, file_path, branch)
            )

        patches = self.composer.compose_patch(extraction_results, branch)

        commit_payload = {
            "repo_id": f"{target_owner}/{target_repo}",
            "branch": branch,
            "commit_message": plan["commit_message"],
            "patches": [p.dict() for p in patches]
        }

        result = self.federation_service.commit_patch(commit_payload)
        return result
