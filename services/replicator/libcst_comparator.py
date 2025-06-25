import libcst as cst
from typing import List
from models.libcst_patch_types import PatchDelta, PatchDeltaType, ChangeClass


class LibCSTDeltaEngine:
    @staticmethod
    def compare(old_code: str, new_code: str) -> List[PatchDelta]:
        old_tree = cst.parse_module(old_code)
        new_tree = cst.parse_module(new_code)

        old_funcs = [n for n in old_tree.body if isinstance(n, cst.FunctionDef)]
        new_funcs = [n for n in new_tree.body if isinstance(n, cst.FunctionDef)]

        deltas = []
        for old_func, new_func in zip(old_funcs, new_funcs):
            deltas.extend(compare_function_defs(old_func, new_func))

        return deltas


def compare_function_defs(old_node: cst.FunctionDef, new_node: cst.FunctionDef) -> List[PatchDelta]:
    """
    Compare two FunctionDef nodes for docstring and signature changes.
    Return a list of PatchDelta instances.
    """
    deltas = []
    old_doc = get_docstring(old_node)
    new_doc = get_docstring(new_node)

    if old_doc != new_doc:
        deltas.append(
            PatchDelta(
                node_type=PatchDeltaType.FUNCTION_DEF.value,
                change_type=ChangeClass.MODIFIED.value,
                detail=f"Docstring changed: '{old_doc}' → '{new_doc}'"
            )
        )
    return deltas


def get_docstring(node: cst.FunctionDef) -> str:
    """
    Safely extract the first docstring from a function.
    """
    if not isinstance(node.body, cst.IndentedBlock):
        return ""
    if not node.body.body:
        return ""
    first = node.body.body[0]
    if isinstance(first, cst.SimpleStatementLine) and first.body and isinstance(first.body[0], cst.Expr):
        expr = first.body[0]
        if isinstance(expr.value, cst.SimpleString):
            return expr.value.evaluated_value
    return ""
