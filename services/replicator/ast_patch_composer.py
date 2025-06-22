import ast
import astunparse
from astdiff.astdiff import compare_ast
from models.federation_schemas import PatchObject

class ASTPatchComposer:
    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold

    def compose_patch(self, old_content: str, new_ast_mutator: callable, file_path: str, base_sha: str) -> PatchObject:
        try:
            old_ast = ast.parse(old_content)
            new_ast = new_ast_mutator(old_ast)
            updated_content = astunparse.unparse(new_ast)
            updated_ast = ast.parse(updated_content)
            compare_ast(old_ast, updated_ast)
        except AssertionError as e:
            raise Exception(f"[Patch Blocked] Semantic mismatch detected: {str(e)}")
        except Exception as e:
            raise Exception(f"[AST Composer Error] {str(e)}")

        return PatchObject(
            file_path=file_path,
            base_sha=base_sha,
            updated_content=updated_content
        )
