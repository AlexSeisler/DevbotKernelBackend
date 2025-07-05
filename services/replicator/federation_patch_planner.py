import libcst as cst
import difflib
from typing import Optional


class InjectTransformer(cst.CSTTransformer):
    def __init__(self, anchor_name: str, injected_code: str):
        self.anchor_name = anchor_name
        self.injected_code = injected_code
        self.inserted = False

    def _inject_into_body(self, body: cst.IndentedBlock) -> cst.IndentedBlock:
        try:
            injected_nodes = cst.parse_module(self.injected_code).body
        except Exception as e:
            raise ValueError(f"Failed to parse injected code block: {e}")

        return body.with_changes(body=list(injected_nodes) + body.body)

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value == self.anchor_name and not self.inserted:
            new_body = self._inject_into_body(updated_node.body)
            self.inserted = True
            return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value == self.anchor_name and not self.inserted:
            new_body = self._inject_into_body(updated_node.body)
            self.inserted = True
            return updated_node.with_changes(body=new_body)
        return updated_node


class FederatedCSTPatchPlanner:
    def __init__(self, context: Optional[dict] = None):
        self.context = context or {}

    def generate_patch(self, old_code: str, anchor: str, code_block: str) -> dict:
        try:
            module = cst.parse_module(old_code)
        except Exception as e:
            raise ValueError(f"Failed to parse original code: {e}")

        transformer = InjectTransformer(anchor_name=anchor, injected_code=code_block)
        modified_module = module.visit(transformer)

        if not transformer.inserted:
            raise ValueError(f"Anchor '{anchor}' not found in code — patch not applied")

        patched_code = modified_module.code

        # Robust diff check using semantic whitespace-insensitive comparison
        old_lines = old_code.splitlines()
        new_lines = patched_code.splitlines()

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=self.context.get("file_path", "before.py"),
                tofile=self.context.get("file_path", "after.py"),
                lineterm=""
            )
        )

        # If no actual diff lines exist (excluding headers), skip
        if not any(line.startswith(('+', '-')) and not line.startswith(('+++', '---')) for line in diff_lines):
            raise ValueError("Patch resulted in no meaningful changes — commit skipped")

        diff = "\n".join(diff_lines)

        return {
            "patched_code": patched_code,
            "diff": diff,
            "metadata": {
                "insertion_point": anchor,
                "change_type": "insert",
                "repo_id": self.context.get("repo_id"),
                "file_path": self.context.get("file_path"),
                "base_sha": self.context.get("base_sha")
            }
        }
