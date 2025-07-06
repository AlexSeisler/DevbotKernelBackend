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

    def leave_Module(self, original_node, updated_node):
        if self.anchor_name == "BOF" and not self.inserted:
            print("[transform] 🎯 Match Anchor: BOF")
            try:
                injected_nodes = cst.parse_module(self.injected_code).body
            except Exception as e:
                raise ValueError(f"[transform] ❌ Failed to parse injected code block: {e}")
            self.inserted = True
            return updated_node.with_changes(body=tuple(list(injected_nodes) + list(updated_node.body)))
        elif self.anchor_name == "EOF" and not self.inserted:
            print("[transform] 🎯 Match Anchor: EOF")
            try:
                injected_nodes = cst.parse_module(self.injected_code).body
            except Exception as e:
                raise ValueError(f"[transform] ❌ Failed to parse injected code block: {e}")
            self.inserted = True
            return updated_node.with_changes(body=tuple(list(updated_node.body) + list(injected_nodes)))
        return updated_node

class FederatedCSTPatchPlanner:
    def __init__(self, context: dict = None):
        self.context = context or {}

    def generate_patch(self, old_code: str, anchor: str, code_block: str) -> dict:
        print("[patch-gen] 🔍 Starting generate_patch")
        try:
            module = cst.parse_module(old_code)
        except Exception as e:
            raise ValueError(f"[patch-gen] ❌ Failed to parse original code: {e}")

        print(f"[patch-gen] 📌 Anchor: {anchor}")
        print(f"[patch-gen] 📄 Injecting Code Block:\n{code_block}")

        # 🚫 Check if anchor already contains the exact code_block
        for node in module.body:
            if isinstance(node, cst.FunctionDef) and node.name.value == anchor:
                # Extract raw code from the function's body safely
                try:
                    anchor_body_code = module.code_for_node(node.body)
                    existing_lines = anchor_body_code.strip().splitlines()
                    if code_block.strip() in [line.strip() for line in existing_lines]:
                        raise ValueError("[patch-gen] ⚠️ Identical code block already exists in anchor — skipping")
                except Exception as e:
                    print(f"[patch-gen] ⚠️ Failed to extract anchor code: {e}")

                if code_block.strip() in [line.strip() for line in existing_lines]:
                    raise ValueError("[patch-gen] ⚠️ Identical code block already exists in anchor — skipping")

        transformer = InjectTransformer(anchor_name=anchor, injected_code=code_block)
        modified_module = module.visit(transformer)

        if not transformer.inserted:
            raise ValueError(f"[patch-gen] ❌ Anchor '{anchor}' not found in code — patch not applied")

        patched_code = modified_module.code

        print("[patch-gen] 🧬 Patched code generated.")
        print("[patch-gen] 🔍 Performing diff check...")

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
                "base_sha": self.context.get("base_sha")
            }
        }
