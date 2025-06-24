import libcst as cst
from services.replicator.libcst_comparator import compare_function_defs
from services.replicator.libcst_patch_types import PatchDelta, PatchASTProposal
from typing import Callable

def compose_patch(old_content: str, new_ast_mutator: Callable[[cst.Module], cst.Module], file_path: str, base_sha: str, manual: bool = False) -> PatchASTProposal:
    """
    Generate a PatchASTProposal using LibCST diffing.
    """
    old_tree = cst.parse_module(old_content)
    new_tree = new_ast_mutator(old_tree)

    # 🚧 Compare docstrings for now
    old_funcs = [n for n in old_tree.body if isinstance(n, cst.FunctionDef)]
    new_funcs = [n for n in new_tree.body if isinstance(n, cst.FunctionDef)]

    deltas = []
    for old, new in zip(old_funcs, new_funcs):
        deltas.extend(compare_function_defs(old, new))

    # Build the PatchASTProposal
    return PatchASTProposal(
        file_path=file_path,
        base_sha=base_sha,
        updated_content=new_tree.code,
        diff_summary=f"{len(deltas)} change(s) detected",
        risk_class="SAFE" if deltas else "NONE",
        risk_score=0.0,
        manual=manual
    )
