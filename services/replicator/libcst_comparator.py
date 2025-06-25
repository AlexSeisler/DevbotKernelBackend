import libcst as cst
from typing import List
from models.libcst_patch_types import PatchDelta, PatchDeltaType, ChangeClass

def compare_function_defs(old_node: cst.FunctionDef, new_node: cst.FunctionDef) -> List[PatchDelta]:
    '\n    Compare two FunctionDef nodes for docstring and signature changes.\n    Return a list of PatchDelta instances.\n    '
    deltas = []
    old_doc = get_docstring(old_node)
    new_doc = get_docstring(new_node)
    if (old_doc != new_doc):
        deltas.append(PatchDelta(node_type=PatchDeltaType.FUNCTION_DEF.value, change_type=ChangeClass.MODIFIED.value, detail=f"Docstring changed: '{old_doc}' → '{new_doc}'"))
    return deltas

def get_docstring(node: cst.FunctionDef) -> str:
    '\n    Safely extract the first docstring from a function.\n    '
    if (not isinstance(node.body, cst.IndentedBlock)):
        return ''
    if (not node.body.body):
        return ''
    first = node.body.body[0]
    if (isinstance(first, cst.SimpleStatementLine) and first.body and isinstance(first.body[0], cst.Expr)):
        expr = first.body[0]
        if isinstance(expr.value, cst.SimpleString):
            return expr.value.evaluated_value
    return ''