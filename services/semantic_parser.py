import ast
import hashlib
import uuid
import multiprocessing

class SemanticParser:

    def parse_python_file(self, file_content, file_path="unknown.py"):
        semantic_nodes = []
        try:
            tree = ast.parse(file_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    decorators = [d.id for d in node.decorator_list if hasattr(d, 'id')]
                    semantic_nodes.append({
                        "node_type": "function",
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "return_type": ast.unparse(node.returns) if node.returns else None,
                        "docstring": ast.get_docstring(node),
                        "decorators": decorators,
                        "code_block": ast.get_source_segment(file_content, node),
                        "file_path": file_path,
                        "line_range": [node.lineno, getattr(node, 'end_lineno', node.lineno)],
                        "uuid": self._generate_uuid(node.name, file_path, node.lineno),
                        "interface_type": "API route" if any("@router." in d for d in decorators) else None
                    })

                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    inherits = [base.id for base in node.bases if hasattr(base, 'id')]
                    decorators = [d.id for d in node.decorator_list if hasattr(d, 'id')]
                    semantic_nodes.append({
                        "node_type": "class",
                        "name": node.name,
                        "methods": methods,
                        "inherits_from": inherits,
                        "docstring": ast.get_docstring(node),
                        "decorators": decorators,
                        "code_block": ast.get_source_segment(file_content, node),
                        "file_path": file_path,
                        "line_range": [node.lineno, getattr(node, 'end_lineno', node.lineno)],
                        "uuid": self._generate_uuid(node.name, file_path, node.lineno),
                        "interface_type": None  # Optional: extend heuristic here too
                    })
        except Exception as e:
            print(f"[SEMANTIC ERROR] Failed parsing {file_path}: {str(e)}")
        return semantic_nodes

    def _generate_uuid(self, name, file_path, lineno):
        seed = f"{name}-{file_path}-{lineno}"
        return hashlib.sha256(seed.encode()).hexdigest()


    def _internal_parse(code: str):
        try:
            tree = ast.parse(code)
            return [{
                "name": "LargeParsedModule",
                "node_type": "module",
                "docstring": ast.get_docstring(tree),
                "args": [],
                "decorators": [],
                "parents": [],
                "returns": None,
                "file_path": None,
                "code_block": code,
                "interface_type": None
            }]
        except Exception as e:
            raise Exception(f"AST parse failed: {e}")


    def parse_large_python_file(code: str, timeout: int = 10):
        with multiprocessing.Pool(1) as pool:
            result = pool.apply_async(_internal_parse, (code,))
            return result.get(timeout=timeout)
