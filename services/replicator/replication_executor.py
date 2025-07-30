# FINAL PRODUCTION-GRADE REPLICATION EXECUTOR


from services.federation_service import FederationService
from services.db.repo_manager import RepoManager
from services.github_service import GitHubService

class ReplicationExecutor:
    def __init__(self):
        self.federation_service = FederationService()
        self.repo_manager = RepoManager()
        self.github_service = GitHubService()

    def _resolve_slug(self, repo_identifier):
        """Return owner/repo slug for a repo identifier.

        The identifier may be a numeric primary key or a slug string.
        """
        if isinstance(repo_identifier, str):
            if repo_identifier.isdigit():
                repo_identifier = int(repo_identifier)
            else:
                return repo_identifier

        if isinstance(repo_identifier, int):
            return self.repo_manager.resolve_repo_id_by_pk(repo_identifier)

        return repo_identifier

    def execute_replication(self, plan):
        print(f"[TRACE] Received plan: {plan}")

        logical_source_id = plan.get("source_repo_id")
        logical_target_id = plan.get("target_repo_id")
        branch = plan.get("target_branch")
        commit_message = plan.get("commit_message")

        source_repo = self._resolve_slug(logical_source_id)
        target_repo = self._resolve_slug(logical_target_id)

        print(f"[TRACE] Normalized source_repo: {source_repo}")
        print(f"[TRACE] Normalized target_repo: {target_repo}")

        source_owner, source_name = source_repo.split("/")
        target_owner, target_name = target_repo.split("/")

        unique_paths = list({m["file_path"] for m in plan["modules"]})
        print(f"[REPLICATION PLAN] Total modules: {len(plan['modules'])}, Unique file paths: {len(unique_paths)}")
        print(f"[REPLICATION FILES] {unique_paths}")

        commit_payloads = []
        for file_path in unique_paths:
            try:
                src_file = self.github_service.get_file(source_owner, source_name, file_path, branch)
                base_sha = self.github_service.get_latest_file_sha(target_owner, target_name, file_path, branch)

                commit_payloads.append({
                    "repo_id": target_repo,
                    "branch": branch,
                    "file_path": file_path,
                    "base_sha": base_sha,
                    "patched_code": src_file["content"],
                    "commit_message": commit_message,
                })
            except Exception as e:
                print(f"[REPLICATION ERROR] Failed to prepare {file_path}: {e}")
                continue

        results = []
        for payload in commit_payloads:
            try:
                result = self.federation_service.commit_patch(payload)
                results.append(result)
            except Exception as e:
                print(f"[REPLICATION ERROR] Failed to commit {payload['file_path']}: {e}")
                continue

        return results
