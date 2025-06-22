# PATCH ENGINE UPGRADE: AST-NATIVE PATCH COMPOSER

import ast
from astdiff import compare_ast_strings

from models.federation_schemas import PatchObject

class ASTPatchComposer:
    def __init__(self):
        self.threshold = 0.0  # Fully lock down Phase 1 — no semantic delta allowed

    def compose_patch(self, old_content: str, new_ast_mutator: callable, file_path: str, base_sha: str) -> PatchObject:
        """
        Composes a patch using AST diff and mutation logic.

        Parameters:
            old_content (str): Original file content
            new_ast_mutator (function): Function that mutates the parsed AST
            file_path (str): File path of the target file
            base_sha (str): GitHub SHA of current file version

        Returns:
            PatchObject: Patch ready for propose-patch call
        """
        try:
            old_ast = ast.parse(old_content)
            mutated_ast = new_ast_mutator(old_ast)
            updated_content = ast.unparse(mutated_ast)
        except Exception as e:
            raise Exception(f"AST patch composition failed: {str(e)}")

        # SEMANTIC SAFETY CHECK (AST DIFF)
        diff_score = compare_ast_strings(old_content, updated_content)
        if diff_score > self.threshold:
            raise Exception(f"Patch rejected — semantic diff score {diff_score:.2f} exceeds threshold {self.threshold:.2f}")

        return PatchObject(
            file_path=file_path,
            base_sha=base_sha,
            updated_content=updated_content
        )
