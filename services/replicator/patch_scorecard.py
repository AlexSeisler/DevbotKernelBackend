import ast
from typing import Dict, List


def generate_patch_scorecard(old_ast: ast.AST, new_ast: ast.AST) -> Dict:
    """
    Analyzes the AST diff between old and new trees and returns a human-readable summary.

    Returns:
        {
            "added_nodes": [...],
            "removed_nodes": [...],
            "modified_functions": [...],
            "summary": "Renamed greet_user to welcome_user"
        }
    """
    def extract_defs(tree: ast.AST) -> Dict[str, ast.FunctionDef]:
        return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    def extract_node_types(tree: ast.AST) -> List[str]:
        return [type(n).__name__ for n in ast.walk(tree)]

    scorecard = {
        "added_nodes": [],
        "removed_nodes": [],
        "modified_functions": [],
        "summary": ""
    }

    old_node_types = set(extract_node_types(old_ast))
    new_node_types = set(extract_node_types(new_ast))

    scorecard["added_nodes"] = list(new_node_types - old_node_types)
    scorecard["removed_nodes"] = list(old_node_types - new_node_types)

    old_funcs = extract_defs(old_ast)
    new_funcs = extract_defs(new_ast)

    for name in old_funcs:
        if name in new_funcs:
            old_args = [a.arg for a in old_funcs[name].args.args]
            new_args = [a.arg for a in new_funcs[name].args.args]
            if old_args != new_args:
                scorecard["modified_functions"].append(name)

    if scorecard["added_nodes"] == [] and scorecard["removed_nodes"] == [] and scorecard["modified_functions"] == []:
        scorecard["summary"] = "Format-only or rename-level change."
    elif scorecard["modified_functions"]:
        scorecard["summary"] = f"Modified function parameters: {', '.join(scorecard['modified_functions'])}"
    else:
        scorecard["summary"] = "Structural or logical patch with new node types."

    return scorecard
