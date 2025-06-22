import ast
import astunparse
from astdiff.diff import compare_ast_strings

from models.federation_schemas import PatchObject

class ASTPatchComposer:
    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold

    def compose_patch(self, old_content: str, new_ast_mutator: callable, file_path: str, base_sha: str) -> PatchObject:
        try:
            old_ast = ast.parse(old_content)
            new_ast = new_ast_mutator(old_ast)
            updated_content = astunparse.unparse(new_ast)
        except Exception as e:
            raise Exception(f"[AST Composer Error] {str(e)}")

        diff_score = compare_ast_strings(old_content, updated_content)
        if diff_score > self.threshold:
            raise Exception(f"[Patch Blocked] Semantic diff score {diff_score:.2f} exceeds threshold {self.threshold:.2f}")

        return PatchObject(
            file_path=file_path,
            base_sha=base_sha,
            updated_content=updated_content
        )