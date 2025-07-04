import base64
from models.federation_schemas import PatchASTProposal
from services.github_service import GitHubService
from services.replicator.federation_patch_planner import FederatedCSTPatchPlanner


class PatchProposalBuilder:
    def build_from_extraction(self, extraction_results, branch, strategy="direct_import", context=None):
        gh = GitHubService()
        patches = []

        for file_path, base_sha, b64_content in extraction_results:
            decoded = base64.b64decode(b64_content).decode('utf-8')
            current = gh.get_file_content(file_path, branch)

            # Skip if no changes
            if current and current.strip() == decoded.strip():
                print(f"[PatchComposer] No-op patch skipped for {file_path}")
                continue

            # LibCST Strategy: Generate safe, scoped patch
            if strategy == "direct_import":
                cst_context = {
                    "repo_id": context.get("repo_id"),
                    "file_path": file_path,
                    "base_sha": base_sha,
                    "target_sha": context.get("target_sha")
                }
                planner = FederatedCSTPatchPlanner(cst_context)
                patch_payload = planner.generate_patch(
                    old_code=current,
                    new_node={"code_block": decoded, "node_name": file_path.split("/")[-1]},
                    anchor=file_path.split("/")[-1].replace(".py", "")
                )

                patch = PatchASTProposal(
                    file_path=file_path,
                    base_sha=base_sha,
                    updated_content=patch_payload["patched_code"],
                    diff=patch_payload["diff"],
                    metadata=patch_payload["metadata"]
                )
                patches.append(patch)
                continue

            # Fallback direct patch (rare)
            patch = PatchASTProposal(
                file_path=file_path,
                base_sha=base_sha,
                updated_content=decoded
            )
            patches.append(patch)

        return patches