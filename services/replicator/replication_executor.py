# FINAL PRODUCTION-GRADE REPLICATION EXECUTOR

from services.replicator.module_extractor import ModuleExtractor
from services.replicator.ast_patch_composer import ASTPatchComposer
from services.replicator.manual_review_queue import submit_to_manual_review_queue
from services.federation_service import FederationService
from services.db.repo_manager import RepoManager
from services.github_service import GitHubService
from models.federation_schemas import CommitPatchRequest

class ReplicationExecutor:
    def __init__(self):
        self.extractor = ModuleExtractor()
        self.ast_composer = ASTPatchComposer()
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

        commit_payloads = []
        for module in plan["modules"]:
            file_path = module["file_path"]
            base_sha = self.github_service.get_latest_file_sha(file_path, branch)
            try:
                old_content = self.github_service.get_file_content(file_path, branch)

                def noop_mutator(tree):
                    return tree  # Replace with GPT logic when ready

                patch = self.ast_composer.compose_patch(
                    old_content=old_content,
                    new_ast_mutator=noop_mutator,
                    file_path=file_path,
                    base_sha=base_sha
                )

                commit_payloads.append(CommitPatchRequest(
                    repo_id=target_repo,
                    branch=branch,
                    file_path=patch.file_path,
                    base_sha=patch.base_sha,
                    updated_content=patch.updated_content,
                    commit_message=commit_message
                ))

            except Exception as e:
                submit_to_manual_review_queue(
                    file_path=file_path,
                    old_content=old_content,
                    new_content="",  # failed mutation, so no update
                    base_sha=base_sha,
                    error_reason=str(e)
                )
                continue

        try:
            results = []
            for payload in commit_payloads:
                result = self.federation_service.commit_patch(payload)
                results.append(result)
            return results
        except Exception as e:
            raise Exception(f"Replication failed: {str(e)}")
