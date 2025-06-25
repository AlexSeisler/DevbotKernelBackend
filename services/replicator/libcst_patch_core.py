import libcst as cst
from services.replicator.libcst_comparator import compare_function_defs
from models.libcst_patch_types import PatchDelta, PatchASTProposal
from typing import Callable, List


def compose_patch(old_content: str, new_ast_mutator: Callable[[cst.Module], cst.Module],
                  file_path: str, base_sha: str, manual: bool = False) -> PatchASTProposal:
    """
    Generate a PatchASTProposal using LibCST diffing.
    """
    old_tree = cst.parse_module(old_content)
    new_tree = new_ast_mutator(old_tree)

    # 🔍 Compare docstrings
    old_funcs = [n for n in old_tree.body if isinstance(n, cst.FunctionDef)]
    new_funcs = [n for n in new_tree.body if isinstance(n, cst.FunctionDef)]

    deltas = []
    for old, new in zip(old_funcs, new_funcs):
        deltas.extend(compare_function_defs(old, new))

    # 🧱 Build the PatchASTProposal
    return PatchASTProposal(
        file_path=file_path,
        base_sha=base_sha,
        updated_content=new_tree.code,
        diff_summary=f"{len(deltas)} change(s) detected" if deltas else "NONE",
        risk_class="SAFE" if deltas else "NONE",
        risk_score=0.0,
        manual=manual
    )


class LibCSTMutator:
    @staticmethod
    def apply(old_code: str, transformer: Callable[[cst.CSTNode], cst.CSTNode]) -> str:
        """
        Applies a CSTTransformer to the parsed LibCST tree.
        Returns the mutated code as a string.
        """
        old_tree = cst.parse_module(old_code)
        new_tree = old_tree.visit(transformer())
        return new_tree.code

class DocstringUpdateTransformer(cst.CSTTransformer):
    """
    Replaces the first docstring in every top-level function with a new string.
    """
    def __init__(self, new_docstring: str):
        self.new_docstring = new_docstring

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        if not isinstance(updated_node.body, cst.IndentedBlock):
            return updated_node

        if not updated_node.body.body:
            return updated_node

        first_stmt = updated_node.body.body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine) and first_stmt.body and isinstance(first_stmt.body[0], cst.Expr):
            expr = first_stmt.body[0]
            if isinstance(expr.value, cst.SimpleString):
                # Replace the docstring
                new_doc = cst.SimpleStatementLine([
                    cst.Expr(cst.SimpleString(f'"""{self.new_docstring}"""'))
                ])
                new_body = [new_doc] + updated_node.body.body[1:]
                return updated_node.with_changes(body=cst.IndentedBlock(body=new_body))
        return updated_node