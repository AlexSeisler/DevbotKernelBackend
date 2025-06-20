from services.replicator.module_extractor import ModuleExtractor
from services.replicator.patch_composer import PatchComposer
from services.federation_service import FederationService
from services.db.repo_manager import RepoManager
from services.github_service import GitHubService
from models.federation_schemas import CommitPatchRequest

class ReplicationExecutor:
    def __init__(self):
        self.extractor = ModuleExtractor()
        self.composer = PatchComposer()
        self.federation_service = FederationService()
        self.repo_manager = RepoManager()
        self.github_service = GitHubService()

    def execute_replication(self, plan):
        source_repo = plan["source_repo_id"]
        target_repo = plan["target_repo_id"]
        branch = plan["target_branch"]
        commit_message = plan["commit_message"]

        source_owner, source_repo_name = source_repo.split("/")
        target_owner, target_repo_name = target_repo.split("/")

        extraction_results = []
        for module in plan["modules"]:
            extraction_results.append(
                self.extractor.fetch_file_content(source_owner, source_repo_name, module["file_path"], branch)
            )

        patches = self.composer.compose_patch(extraction_results, branch)

        commit_payloads = []
        for p in patches:
            file_path = p.file_path
            base_sha = self.github_service.get_latest_file_sha(file_path, branch)
            updated_content = p.updated_content

            commit_payloads.append(CommitPatchRequest(
                repo_id=target_repo,
                branch=branch,
                file_path=file_path,
                base_sha=base_sha,
                updated_content=updated_content,
                commit_message=commit_message
            ))

        try:
            results = []
            for payload in commit_payloads:
                result = self.federation_service.commit_patch(payload)
                results.append(result)
            return results
        except Exception as e:
            raise Exception(f"Replication failed: {str(e)}")