# PATCH ENGINE UPGRADE: AST-NATIVE PATCH COMPOSER

import ast
from models.federation_schemas import PatchObject

class ASTPatchComposer:
    def __init__(self):
        pass

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

        if len(updated_content.strip().splitlines()) < 0.8 * len(old_content.strip().splitlines()):
            raise Exception("Refused to commit patch — possible file truncation detected.")

        return PatchObject(
            file_path=file_path,
            base_sha=base_sha,
            updated_content=updated_content
        )
