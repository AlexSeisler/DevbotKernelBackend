import ast
import astunparse
from astdiff.astdiff import compare_ast
from models.federation_schemas import PatchObject

class ASTPatchComposer:
    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold

    def compose_patch(self, old_content: str, new_ast_mutator: callable, file_path: str, base_sha: str, manual: bool = False) -> PatchObject:
        if manual:
            # Bypass AST diff and return trusted patch
            updated_ast = ast.parse(old_content)
            updated_content = astunparse.unparse(updated_ast)
            return PatchObject(
                file_path=file_path,
                base_sha=base_sha,
                updated_content=updated_content,
                risk_class="MANUAL",
                diff_summary="Manual override: patch composer bypassed"
            )

        try:
            old_ast = ast.parse(old_content)
            new_ast = new_ast_mutator(old_ast)
            updated_content = astunparse.unparse(new_ast)
            updated_ast = ast.parse(updated_content)

            from .risk_classifier import classify_ast_diff
            from .patch_scorecard import generate_patch_scorecard

            risk_class = classify_ast_diff(old_ast, updated_ast)
            scorecard = generate_patch_scorecard(old_ast, updated_ast)

            return PatchObject(
                file_path=file_path,
                base_sha=base_sha,
                updated_content=updated_content,
                risk_class=risk_class,
                diff_summary=scorecard["summary"]
            )

        except Exception as e:
            raise Exception(f"[AST Composer Error] {str(e)}")
