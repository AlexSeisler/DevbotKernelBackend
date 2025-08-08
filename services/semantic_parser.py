import hashlib
import multiprocessing
import libcst as cst
from typing import List, Dict, Optional

LARGE_FILE_THRESHOLD = 50000  # ~50 KB


class BaseSemanticParser:
    def parse(self, file_content: str, file_path: str) -> list[dict]:
        """
        Returns a list of semantic node dictionaries in unified schema.
        """
        raise NotImplementedError


class LibCSTSemanticParser(BaseSemanticParser):

    def _generate_uuid(self, name: str, file_path: str, lineno: int) -> str:
        seed = f"{name}-{file_path}-{lineno}"
        return hashlib.sha256(seed.encode()).hexdigest()

    def _extract_docstring(self, node) -> Optional[str]:
        if hasattr(node, "body") and hasattr(node.body, "body") and node.body.body:
            first_stmt = node.body.body[0]
            if isinstance(first_stmt, cst.SimpleStatementLine):
                first_expr = first_stmt.body[0]
                if isinstance(first_expr, cst.Expr) and isinstance(first_expr.value, cst.SimpleString):
                    return first_expr.value.evaluated_value
        return None

    def _build_collector(self, source: str, file_path: str, module: cst.Module):
        parser_self = self

        class Collector(cst.CSTVisitor):
            def __init__(self):
                self.nodes: List[Dict] = []
                self.imports: List[str] = []

            # === IMPORTS ===
            def visit_Import(self, node: cst.Import):
                for name in node.names:
                    self.imports.append(name.name.value)
                print(f"[DEBUG] Collected Import: {self.imports}")

            def visit_ImportFrom(self, node: cst.ImportFrom):
                module_name = node.module.value if node.module else ""
                for name in node.names:
                    import_name = name.name.value
                    full_import = f"{module_name}.{import_name}" if module_name else import_name
                    self.imports.append(full_import)
                print(f"[DEBUG] Collected Import: {self.imports}")

            # === FUNCTIONS ===
            def _handle_function(self, node, async_fn=False):
                decorators = [module.code_for_node(d.decorator) for d in node.decorators]
                args = [p.name.value for p in node.params.params]
                returns = module.code_for_node(node.returns.annotation) if node.returns else None

                node_dict = {
                    "node_type": "async_function" if async_fn else "function",
                    "name": node.name.value,
                    "language": "python",
                    "imports": list(set(self.imports)),
                    "decorators": decorators,
                    "docstring": parser_self._extract_docstring(node),
                    "args": args,
                    "return_type": returns,
                    "code_block": module.code_for_node(node),
                    "start_line": getattr(node, "start", None).line if hasattr(node, "start") else None,
                    "end_line": getattr(node, "end", None).line if hasattr(node, "end") else None,
                    "uuid": parser_self._generate_uuid(node.name.value, file_path, getattr(node, "start", None).line if hasattr(node, "start") else 0),
                    "interface_type": None
                }

                # Interface type detection
                if any("router" in d or "app." in d for d in decorators):
                    node_dict["interface_type"] = "API route"

                print(f"[DEBUG] Visiting {'AsyncFunctionDef' if async_fn else 'FunctionDef'}: {node.name.value} → {node_dict}")
                self.nodes.append(node_dict)

            def visit_FunctionDef(self, node: cst.FunctionDef):
                self._handle_function(node, async_fn=False)

            def visit_AsyncFunctionDef(self, node: cst.AsyncFunctionDef):
                self._handle_function(node, async_fn=True)

            # === CLASSES ===
            def visit_ClassDef(self, node: cst.ClassDef):
                decorators = [module.code_for_node(d.decorator) for d in node.decorators]
                inherits = [module.code_for_node(base) for base in node.bases]

                methods = []
                for b in node.body.body:
                    if isinstance(b, cst.FunctionDef):
                        methods.append(b.name.value)
                    elif isinstance(b, cst.AsyncFunctionDef):
                        methods.append(b.name.value)

                node_dict = {
                    "node_type": "class",
                    "name": node.name.value,
                    "language": "python",
                    "imports": list(set(self.imports)),
                    "decorators": decorators,
                    "docstring": parser_self._extract_docstring(node),
                    "methods": methods,
                    "inherits_from": inherits,
                    "code_block": module.code_for_node(node),
                    "start_line": getattr(node, "start", None).line if hasattr(node, "start") else None,
                    "end_line": getattr(node, "end", None).line if hasattr(node, "end") else None,
                    "uuid": parser_self._generate_uuid(node.name.value, file_path, getattr(node, "start", None).line if hasattr(node, "start") else 0),
                    "interface_type": None
                }

                print(f"[DEBUG] Visiting ClassDef: {node.name.value} → {node_dict}")
                self.nodes.append(node_dict)

        return Collector()

    def _internal_parse_libcst(self, code: str, file_path: str):
        print(f"[DEBUG] LibCSTSemanticParser.parse called for {file_path}")
        module = cst.parse_module(code)
        collector = self._build_collector(code, file_path, module)
        module.visit(collector)
        print(f"[DEBUG] Extracted {len(collector.nodes)} nodes from {file_path}")
        return collector.nodes

    def parse_large_python_file_libcst(self, code: str, file_path: str, timeout: int = 10):
        with multiprocessing.Pool(1) as pool:
            result = pool.apply_async(self._internal_parse_libcst, (code, file_path))
            return result.get(timeout=timeout)

    def parse(self, file_content: str, file_path: str) -> list[dict]:
        if len(file_content) > LARGE_FILE_THRESHOLD:
            return self.parse_large_python_file_libcst(file_content, file_path)
        else:
            return self._internal_parse_libcst(file_content, file_path)
