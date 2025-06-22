import ast

def classify_ast_diff(old_ast: ast.AST, new_ast: ast.AST) -> str:
    """
    Classifies the semantic risk of an AST patch based on structural deltas.
    Returns:
        - "SAFE": only small additions
        - "RENAME": similar structure but renamed nodes
        - "STRUCTURAL": added/removed FunctionDef or ClassDef
        - "LOGIC": logic structure changed (If, For, Try, While)
        - "DEEP": argument-level changes
    """
    old_funcs = {node.name for node in ast.walk(old_ast) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    new_funcs = {node.name for node in ast.walk(new_ast) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}

    added = new_funcs - old_funcs
    removed = old_funcs - new_funcs

    if removed:
        return "STRUCTURAL"
    if added:
        return "SAFE"
    if old_funcs != new_funcs:
        return "RENAME"

    old_nodes = list(ast.walk(old_ast))
    new_nodes = list(ast.walk(new_ast))

    old_types = {type(n).__name__ for n in old_nodes}
    new_types = {type(n).__name__ for n in new_nodes}

    if old_types != new_types:
        if any(n in new_types.union(old_types) for n in ["If", "While", "For", "Try"]):
            return "LOGIC"
        if any(n in new_types.union(old_types) for n in ["arguments", "arg"]):
            return "DEEP"

    return "SAFE"
