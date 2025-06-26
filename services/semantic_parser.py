import ast

class SemanticParser:

    import ast
import hashlib
import uuid

class SemanticParser:

    def parse_python_file(self, file_content, file_path="unknown.py"):
        semantic_nodes = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    semantic_nodes.append({
                        "node_type": "function",
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "returns": getattr(node.returns, 'id', None) if node.returns else None,
                        "docstring": ast.get_docstring(node),
                        "decorators": [d.id for d in node.decorator_list if hasattr(d, 'id')],
                        "file_path": file_path,
                        "line_range": (node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        "uuid": self._generate_uuid(node.name, file_path, node.lineno)
                    })

                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    inherits = [base.id for base in node.bases if hasattr(base, 'id')]
                    semantic_nodes.append({
                        "node_type": "class",
                        "name": node.name,
                        "methods": methods,
                        "inherits_from": inherits,
                        "docstring": ast.get_docstring(node),
                        "decorators": [d.id for d in node.decorator_list if hasattr(d, 'id')],
                        "file_path": file_path,
                        "line_range": (node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        "uuid": self._generate_uuid(node.name, file_path, node.lineno)
                    })
        except Exception as e:
            print(f"[SEMANTIC ERROR] Failed parsing {file_path}: {str(e)}")
        return semantic_nodes

    def _generate_uuid(self, name, file_path, lineno):
        seed = f"{name}-{file_path}-{lineno}"
        return hashlib.sha256(seed.encode()).hexdigest()
