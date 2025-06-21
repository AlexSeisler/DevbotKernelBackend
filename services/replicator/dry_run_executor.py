# DRY RUN WRAPPER FOR PATCH EXECUTION

from services.replicator.replication_executor import ReplicationExecutor

def execute_replication_dry_run(plan):
    executor = ReplicationExecutor()
    source_repo = plan["source_repo_id"]
    branch = plan["target_branch"]

    for module in plan["modules"]:
        file_path = module["file_path"]
        print("🔍 DRY RUN PATCH PREVIEW:", file_path)

        try:
            base_sha = executor.github_service.get_latest_file_sha(file_path, branch)
            old_content = executor.github_service.get_file_content(file_path, branch)

            def noop_mutator(tree):
                return tree  # preview only

            patch = executor.ast_composer.compose_patch(
                old_content=old_content,
                new_ast_mutator=noop_mutator,
                file_path=file_path,
                base_sha=base_sha
            )

            print("✅ PATCH VALID")
            print("--- PATCH CONTENT START ---")
            print(patch.updated_content[:200])  # preview
            print("--- PATCH CONTENT END ---\n")
        except Exception as e:
            print(f"[DRY RUN ERROR] {file_path}: {str(e)}")
