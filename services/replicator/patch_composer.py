# PATCH PROPOSAL BUILDER (renamed from ASTPatchComposerV2)

import base64
from models.federation_schemas import PatchASTProposal

class PatchProposalBuilder:
    def build_from_extraction(self, extraction_results, branch):
        patches = []
        for file_path, base_sha, b64_content in extraction_results:
            decoded = base64.b64decode(b64_content).decode('utf-8')
            patch = PatchASTProposal(
                file_path=file_path,
                base_sha=base_sha,
                updated_content=decoded
            )
            patches.append(patch)
        return patches