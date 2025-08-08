import hashlib
import multiprocessing
import libcst as cst
from libcst.metadata import PositionProvider
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

    def _build_collector(self, source: str, file_path: str, module: cst.Module, wrapper: cst.metadata.MetadataWrapper):
        parser_self = self

        class Collector(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (PositionProvider,)

            def __init__(self):
                self.nodes: List[Dict] = []
                self.imports: List[str] = []

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
                print(f"[DEBUG] Collected ImportFrom: {self.imports}")

            def visit_FunctionDef(self, node: cst.FunctionDef):
                print(f"[DEBUG] Visiting FunctionDef: {node.name.value} ({type(node)})")
                decorators = [module.code_for_node(d.decorator) for d in node.decorators]
                args = [p.name.value for p in node.params.params]
                returns = module.code_for_node(node.returns.annotation) if node.returns else None

                pos = self.get_metadata(PositionProvider, node)
                self.nodes.append({
                    "node_type": "function",
                    "name": node.name.value,
                    "language": "python",
                    "imports": self.imports.copy(),
                    "decorators": decorators,
                    "docstring": parser_self._extract_docstring(node),
                    "args": args,
                    "return_type": returns,
                    "source_code": module.code_for_node(node),
                    "code_block": module.code_for_node(node),
                    "start_line": pos.start.line,
                    "end_line": pos.end.line,
                    "uuid": parser_self._generate_uuid(node.name.value, file_path, pos.start.line),
                    "interface_type": "API route" if any("router" in d for d in decorators) else None
                })

            def visit_ClassDef(self, node: cst.ClassDef):
                print(f"[DEBUG] Visiting ClassDef: {node.name.value} ({type(node)})")
                decorators = [module.code_for_node(d.decorator) for d in node.decorators]
                inherits = [module.code_for_node(base) for base in node.bases]
                methods = [
                    b.name.value for b in node.body.body
                    if isinstance(b, cst.FunctionDef)
                ]

                pos = self.get_metadata(PositionProvider, node)
                self.nodes.append({
                    "node_type": "class",
                    "name": node.name.value,
                    "language": "python",
                    "imports": self.imports.copy(),
                    "decorators": decorators,
                    "docstring": parser_self._extract_docstring(node),
                    "methods": methods,
                    "inherits_from": inherits,
                    "source_code": module.code_for_node(node),
                    "code_block": module.code_for_node(node),
                    "start_line": pos.start.line,
                    "end_line": pos.end.line,
                    "uuid": parser_self._generate_uuid(node.name.value, file_path, pos.start.line),
                    "interface_type": None
                })

        return Collector()

    def _internal_parse_libcst(self, code: str, file_path: str):
        print(f"[DEBUG] Parsing file in LibCST parser: {file_path}")
        wrapper = cst.metadata.MetadataWrapper(cst.parse_module(code))
        collector = self._build_collector(code, file_path, wrapper.module, wrapper)
        wrapper.visit(collector)
        print(f"[DEBUG] Extracted {len(collector.nodes)} nodes from {file_path}")
        return collector.nodes

    def parse_large_python_file_libcst(self, code: str, file_path: str, timeout: int = 10):
        print(f"[DEBUG] Large file parse triggered for {file_path}")
        with multiprocessing.Pool(1) as pool:
            result = pool.apply_async(self._internal_parse_libcst, (code, file_path))
            return result.get(timeout=timeout)

    def parse(self, file_content: str, file_path: str) -> list[dict]:
        print(f"[DEBUG] LibCSTSemanticParser.parse called for {file_path}")
        if len(file_content) > LARGE_FILE_THRESHOLD:
            return self.parse_large_python_file_libcst(file_content, file_path)
        else:
            return self._internal_parse_libcst(file_content, file_path)
