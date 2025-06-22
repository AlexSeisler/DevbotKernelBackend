# PATCH PROPOSAL BUILDER (renamed from ASTPatchComposerV2)

import base64
from models.federation_schemas import PatchASTProposal
from services.github_service import GitHubService

class PatchProposalBuilder:
    def build_from_extraction(self, extraction_results, branch):
        gh = GitHubService()
        patches = []

        for file_path, base_sha, b64_content in extraction_results:
            decoded = base64.b64decode(b64_content).decode('utf-8')

            # BYPASS AST composer if manual mode is active
            if hasattr(self, "manual") and self.manual:
                patch = PatchASTProposal(
                    file_path=file_path,
                    base_sha=base_sha,
                    updated_content=decoded
                )
                patches.append(patch)
                continue

            # Otherwise check for no-op
            current = gh.get_file_content(file_path, branch)
            if current and current.strip() == decoded.strip():
                print(f"[PatchComposer] No-op patch skipped for {file_path}")
                continue

            patch = PatchASTProposal(
                file_path=file_path,
                base_sha=base_sha,
                updated_content=decoded
            )
            patches.append(patch)



        return patches
