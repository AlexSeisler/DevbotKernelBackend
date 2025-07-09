# PATCH — federation_patch_planner.py
import libcst as cst
import difflib
from typing import Optional
import textwrap


class InjectTransformer(cst.CSTTransformer):
    def __init__(self, anchor_path: list, injected_code: str):
        self.anchor_path = anchor_path
        self.injected_code = injected_code
        self.inserted = False
        self.current_path = []
        self.nesting_level = 0

    def _inject_into_body(self, body: cst.BaseSuite) -> cst.BaseSuite:
        indent = "    " * self.nesting_level
        indented_code = textwrap.indent(self.injected_code.strip(), indent)

        try:
            print(f"[transform] 🧪 Parsing injected code at depth {self.nesting_level}:\n{indented_code}")
            injected_nodes = cst.parse_module(indented_code).body
        except Exception as e:
            raise ValueError(f"[transform] ❌ Failed to parse injected code block:\n{indented_code}\nError: {e}")

        if isinstance(body, cst.IndentedBlock):
            print(f"[transform] ✅ Appending to IndentedBlock (nest={self.nesting_level})")
            return body.with_changes(body=tuple(injected_nodes + list(body.body)))
        elif isinstance(body, cst.SimpleStatementSuite):
            print(f"[transform] 🔁 Wrapping new IndentedBlock from SimpleStatementSuite")
            return cst.IndentedBlock(body=list(injected_nodes) + list(body.body))
        else:
            raise ValueError(f"[transform] ❌ Unsupported block type: {type(body)}")

    def _check_and_inject(self, node_name: str, updated_node, body: Optional[cst.BaseSuite]):
        print(f"[transform] 🔍 Checking node: {node_name} — Current path: {self.current_path}")
        print(f"[transform] 📏 Matching: expected={self.anchor_path} actual={self.current_path}")

        if self.current_path == self.anchor_path and not self.inserted:
            print(f"[transform] 🎯 Anchor match! Inserting into: {' → '.join(self.current_path)}")
            self.nesting_level = len(self.anchor_path)
            if not body:
                raise ValueError(f"[transform] ❌ Cannot inject — '{node_name}' has no body")

            try:
                print(f"[transform] 💥 Injection Triggered — Nesting Level: {self.nesting_level}")
                new_body = self._inject_into_body(body)
                self.inserted = True
                return updated_node.with_changes(body=new_body)
            except Exception as e:
                raise ValueError(f"[transform] ❌ Injection failed for '{node_name}': {e}")
        else:
            print(f"[transform] ⏭️ No match for path: {' → '.join(self.current_path)}")

        return updated_node

    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_path.append(node.name.value)

    def leave_ClassDef(self, original_node, updated_node):
        result = self._check_and_inject(original_node.name.value, updated_node, updated_node.body)
        self.current_path.pop()
        return result

    def visit_FunctionDef(self, node: cst.FunctionDef):
        self.current_path.append(node.name.value)

    def leave_FunctionDef(self, original_node, updated_node):
        result = self._check_and_inject(original_node.name.value, updated_node, updated_node.body)
        self.current_path.pop()
        return result

    def leave_Module(self, original_node, updated_node):
        print(f"[transform] 📦 leave_Module — anchor_path: {self.anchor_path}")
        if self.anchor_path == ["BOF"] and not self.inserted:
            try:
                print(f"[transform] ✨ Injecting at BOF")
                injected_nodes = cst.parse_module(self.injected_code.strip()).body
                self.inserted = True
                return updated_node.with_changes(body=tuple(injected_nodes + list(updated_node.body)))
            except Exception as e:
                raise ValueError(f"[transform] ❌ BOF injection failed: {e}")

        elif self.anchor_path == ["EOF"] and not self.inserted:
            try:
                print(f"[transform] ✨ Injecting at EOF")
                injected_nodes = cst.parse_module(self.injected_code.strip()).body
                self.inserted = True
                return updated_node.with_changes(body=tuple(list(updated_node.body) + list(injected_nodes)))
            except Exception as e:
                raise ValueError(f"[transform] ❌ EOF injection failed: {e}")

        print(f"[transform] 🧩 No module-level injection performed")
        return updated_node


class FederatedCSTPatchPlanner:
    def __init__(self, context: dict = None):
        self.context = context or {}

    def generate_patch(self, old_code: str, anchor: str, code_block: str) -> dict:
        print("[patch-gen] 🔍 Starting generate_patch")
        old_lines = old_code.splitlines()
        anchor_lines = self.context.get("anchor_lines")
        anchor_path = self.context.get("anchor_path", [anchor])

        try:
            module = cst.parse_module(old_code)
        except Exception as e:
            raise ValueError(f"[patch-gen] ❌ Failed to parse original source: {e}")

        transformer = InjectTransformer(anchor_path=anchor_path, injected_code=code_block)
        modified_module = module.visit(transformer)

        if not transformer.inserted:
            raise ValueError(f"[patch-gen] ❌ Anchor path '{' → '.join(anchor_path)}' not found — patch not applied")

        patched_code = modified_module.code
        print("[patch-gen] 🧬 Patched full file generated.")

        diff_lines = list(
            difflib.unified_diff(
                old_code.splitlines(),
                patched_code.splitlines(),
                fromfile=self.context.get("file_path", "before.py"),
                tofile=self.context.get("file_path", "after.py"),
                lineterm=""
            )
        )
        if not any(line.startswith(('+', '-')) and not line.startswith(('+++', '---')) for line in diff_lines):
            raise ValueError("[patch-gen] ⚠️ Patch resulted in no meaningful changes — commit skipped")

        return {
            "patched_code": patched_code,
            "diff": "\n".join(diff_lines),
            "metadata": {
                "insertion_point": " → ".join(anchor_path),
                "change_type": "insert",
                "repo_id": self.context.get("repo_id"),
                "file_path": self.context.get("file_path"),
                "base_sha": self.context.get("base_sha"),
                "anchor_lines": anchor_lines,
                "anchor_path": anchor_path
            }
        }
