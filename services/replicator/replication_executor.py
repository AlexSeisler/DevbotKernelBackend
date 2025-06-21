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

        # Deduplicate by file path
        unique_paths = list({m["file_path"] for m in plan["modules"]})
        print(f"[REPLICATION PLAN] Total modules: {len(plan['modules'])}, Unique file paths: {len(unique_paths)}")
        print(f"[REPLICATION FILES] {unique_paths}")

        extraction_results = []
        for path in unique_paths:
            try:
                result = self.extractor.fetch_file_content(source_owner, source_repo_name, path, branch)
                extraction_results.append(result)
            except Exception as e:
                print(f"[REPLICATION ERROR] Failed to extract {path}: {e}")

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
