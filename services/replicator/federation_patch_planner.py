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
            raise ValueError(f"[transform] ❌ Failed to parse injected code block: {e}")

        return body.with_changes(body=tuple(list(injected_nodes) + list(body.body)))

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value == self.anchor_name and not self.inserted:
            print(f"[transform] 🎯 Match Function: {self.anchor_name}")
            new_body = self._inject_into_body(updated_node.body)
            self.inserted = True
            return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value == self.anchor_name and not self.inserted:
            print(f"[transform] 🎯 Match Class: {self.anchor_name}")
            new_body = self._inject_into_body(updated_node.body)
            self.inserted = True
            return updated_node.with_changes(body=new_body)
        return updated_node


class FederatedCSTPatchPlanner:
    def __init__(self, context: dict = None):
        self.context = context or {}

    def generate_patch(self, old_code: str, anchor: str, code_block: str) -> dict:
        print("[patch-gen] 🔍 Starting generate_patch")

        old_lines = old_code.splitlines()
        anchor_lines = self.context.get("anchor_lines")  # Optional [start, end]

        if anchor_lines:
            start, end = anchor_lines
            print(f"[patch-gen] 🎯 Using anchor_lines: {start}–{end}")
            chunk_lines = old_lines[start - 1:end]
            chunk_code = "\n".join(chunk_lines)
        else:
            print("[patch-gen] 📦 Using full file for patching")
            chunk_code = old_code

        try:
            module = cst.parse_module(chunk_code)
        except Exception as e:
            raise ValueError(f"[patch-gen] ❌ Failed to parse target code: {e}")

        print(f"[patch-gen] 📌 Anchor: {anchor}")
        print(f"[patch-gen] 📄 Injecting Code Block:\n{code_block}")

        transformer = InjectTransformer(anchor_name=anchor, injected_code=code_block)
        modified_module = module.visit(transformer)

        if not transformer.inserted:
            raise ValueError(f"[patch-gen] ❌ Anchor '{anchor}' not found in code — patch not applied")

        patched_chunk = modified_module.code
        print("[patch-gen] 🧬 Patched chunk generated.")

        # Reconstruct final patched_code
        if anchor_lines:
            prefix = old_lines[:start - 1]
            suffix = old_lines[end:]
            final_lines = prefix + patched_chunk.splitlines() + suffix
            patched_code = "\n".join(final_lines)
        else:
            patched_code = patched_chunk

        print("[patch-gen] 🔍 Performing diff check...")
        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                patched_code.splitlines(),
                fromfile=self.context.get("file_path", "before.py"),
                tofile=self.context.get("file_path", "after.py"),
                lineterm=""
            )
        )

        if not any(line.startswith(('+', '-')) and not line.startswith(('+++', '---')) for line in diff_lines):
            raise ValueError("[patch-gen] ⚠️ Patch resulted in no meaningful changes — commit skipped")

        diff = "\n".join(diff_lines)
        print("[patch-gen] ✅ Diff generated.")

        return {
            "patched_code": patched_code,
            "diff": diff,
            "metadata": {
                "insertion_point": anchor,
                "change_type": "insert",
                "repo_id": self.context.get("repo_id"),
                "file_path": self.context.get("file_path"),
                "base_sha": self.context.get("base_sha"),
                "anchor_lines": anchor_lines
            }
        }
