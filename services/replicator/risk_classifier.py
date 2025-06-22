import ast

def classify_ast_diff(old_ast: ast.AST, new_ast: ast.AST) -> str:
    """
    Heuristically classify the semantic risk of a proposed AST patch.
    Returns one of:
    - 'SAFE'
    - 'RENAME'
    - 'STRUCTURAL'
    - 'LOGIC'
    - 'DEEP'
    """
    # Basic counters
    added = []
    removed = []
    renamed = []

    old_nodes = list(ast.walk(old_ast))
    new_nodes = list(ast.walk(new_ast))

    old_types = set(type(n).__name__ for n in old_nodes)
    new_types = set(type(n).__name__ for n in new_nodes)

    added = new_types - old_types
    removed = old_types - new_types

    if any(n in added or n in removed for n in ["If", "While", "For", "Try"]):
        return "LOGIC"
    if any(n in added or n in removed for n in ["FunctionDef", "ClassDef"]):
        return "STRUCTURAL"
    if any(n in added or n in removed for n in ["arguments", "arg"]):
        return "DEEP"

    # Heuristic for rename: mostly same structure, no logic
    if old_types == new_types:
        return "RENAME"

    return "SAFE"
