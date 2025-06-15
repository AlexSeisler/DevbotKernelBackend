import ast

class SemanticParser:

    def parse_python_file(self, file_content):
        semantic_nodes = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    semantic_nodes.append({
                        "node_type": "function",
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for body_item in node.body:
                        if isinstance(body_item, ast.FunctionDef):
                            methods.append(body_item.name)
                    inherits = [base.id for base in node.bases if hasattr(base, 'id')]
                    semantic_nodes.append({
                        "node_type": "class",
                        "name": node.name,
                        "methods": methods,
                        "inherits_from": inherits,
                        "docstring": ast.get_docstring(node)
                    })
        except Exception as e:
            print(f"[ERROR] Semantic parsing failed: {str(e)}")

        return semantic_nodes
