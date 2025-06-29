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
        print(f"[TRACE] Received plan: {plan}")
        logical_source_id = plan.get("source_repo_id")
        logical_target_id = plan.get("target_repo_id")
        branch = plan.get("target_branch")
        commit_message = plan.get("commit_message")

        print(f"[TRACE] Raw source_repo_id: {logical_source_id} ({type(logical_source_id)})")
        print(f"[TRACE] Raw target_repo_id: {logical_target_id} ({type(logical_target_id)})")

        # Split early for GitHub use
        source_owner, source_repo_name = logical_source_id.split("/")
        target_owner, target_repo_name = logical_target_id.split("/")

        # Normalize to integer repo IDs
        source_repo = self.repo_manager.resolve_repo_id_by_pk(logical_source_id) if isinstance(logical_source_id, str) else logical_source_id
        target_repo = self.repo_manager.resolve_repo_id_by_pk(logical_target_id) if isinstance(logical_target_id, str) else logical_target_id

        print(f"[TRACE] Normalized source_repo_id: {source_repo} ({type(source_repo)})")
        print(f"[TRACE] Normalized target_repo_id: {target_repo} ({type(target_repo)})")



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
                    return tree

                patch = self.ast_composer.compose_patch(
                    old_content=old_content,
                    new_ast_mutator=noop_mutator,
                    file_path=file_path,
                    base_sha=base_sha,
                    manual=True  # Signal override to trust updated content
                )


                commit_payloads.append(CommitPatchRequest(
                    repo_id=target_repo,
                    branch=branch,
                    file_path=patch.file_path,
                    base_sha=patch.base_sha,
                    updated_content=patch.updated_content,
                    commit_message=commit_message
                ))
                summary = {
                    "attempted": len(commit_payloads),
                    "committed": 0,
                    "skipped_no_op": 0,
                    "errors": []
                }

                for payload in commit_payloads:
                    try:
                        current = self.github_service.get_file_content(payload.file_path, payload.branch)
                        if current.strip() == payload.updated_content.strip():
                            print(f"[REPLICATION] Skipped no-op commit: {payload.file_path}")
                            summary["skipped_no_op"] += 1
                            continue

                        result = self.federation_service.commit_patch(payload)
                        summary["committed"] += 1

                    except Exception as e:
                        summary["errors"].append({
                            "file": payload.file_path,
                            "error": str(e)
                        })

                print(f"[REPLICATION COMPLETE] Commits: {summary['committed']}, Skipped: {summary['skipped_no_op']}, Errors: {len(summary['errors'])}")
                return summary

            except Exception as e:
                submit_to_manual_review_queue(
                    file_path=file_path,
                    old_content=old_content,
                    new_content="",
                    base_sha=base_sha,
                    error_reason=str(e)
                )
                continue

        try:
            results = []
            for payload in commit_payloads:
                # Fetch current GitHub file content for safety
                current_content = self.github_service.get_file_content(payload.file_path, payload.branch)

                if current_content.strip() == payload.updated_content.strip():
                    print(f"[REPLICATION] Skipped no-op commit: {payload.file_path}")
                    continue

                result = self.federation_service.commit_patch(payload)
                results.append(result)

            return results
        except Exception as e:
            raise Exception(f"Replication failed: {str(e)}")
