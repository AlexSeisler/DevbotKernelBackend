import libcst as cst
import difflib
from typing import Optional

class InjectTransformer(cst.CSTTransformer):
    def __init__(self, anchor_path: list, injected_code: str):
        self.anchor_path = anchor_path
        self.injected_code = injected_code
        self.inserted = False
        self.current_path = []

    def _inject_into_body(self, body: cst.BaseSuite) -> cst.BaseSuite:
        try:
            injected_nodes = cst.parse_module(self.injected_code).body
        except Exception as e:
            raise ValueError(f"[transform] ❌ Failed to parse injected code block: {e}")

        # Support both IndentedBlock and SimpleStatementSuite
        if isinstance(body, cst.IndentedBlock):
            return body.with_changes(body=tuple(list(injected_nodes) + list(body.body)))
        elif isinstance(body, cst.SimpleStatementSuite):
            return cst.IndentedBlock(body=list(injected_nodes) + list(body.body))
        else:
            raise ValueError(f"[transform] ❌ Unsupported block type for injection: {type(body)}")

    def _check_and_inject(self, node_name: str, updated_node, body: cst.BaseSuite):
        self.current_path.append(node_name)
        print(f"[transform-debug] Entering: {node_name}")
        print(f"[transform-debug] Current path: {' → '.join(self.current_path)}")
        print(f"[transform-debug] Target anchor_path: {' → '.join(self.anchor_path)}")

        if self.current_path == self.anchor_path and not self.inserted:
            print(f"[transform] 🎯 Match Path: {' → '.join(self.anchor_path)}")
            new_body = self._inject_into_body(body)
            self.inserted = True
            return updated_node.with_changes(body=new_body)

        return updated_node

    def leave_FunctionDef(self, original_node, updated_node):
        result = self._check_and_inject(original_node.name.value, updated_node, updated_node.body)
        self.current_path.pop()
        print(f"[transform-debug] Leaving Function: {original_node.name.value}")
        return result

    def leave_ClassDef(self, original_node, updated_node):
        result = self._check_and_inject(original_node.name.value, updated_node, updated_node.body)
        self.current_path.pop()
        print(f"[transform-debug] Leaving Class: {original_node.name.value}")
        return result

    def leave_Module(self, original_node, updated_node):
        if self.anchor_path == ["BOF"] and not self.inserted:
            print("[transform] 🎯 Match Anchor: BOF")
            try:
                injected_nodes = cst.parse_module(self.injected_code).body
            except Exception as e:
                raise ValueError(f"[transform] ❌ Failed to parse injected code block: {e}")
            self.inserted = True
            return updated_node.with_changes(body=tuple(list(injected_nodes) + list(updated_node.body)))
        elif self.anchor_path == ["EOF"] and not self.inserted:
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

        old_lines = old_code.splitlines()
        anchor_lines = self.context.get("anchor_lines")
        anchor_path = self.context.get("anchor_path", [anchor])  # Fallback to single name

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

        print(f"[patch-gen] 📌 Anchor Path: {' → '.join(anchor_path)}")
        print(f"[patch-gen] 📄 Injecting Code Block:\n{code_block}")

        transformer = InjectTransformer(anchor_path=anchor_path, injected_code=code_block)
        modified_module = module.visit(transformer)

        if not transformer.inserted:
            raise ValueError(f"[patch-gen] ❌ Anchor path '{' → '.join(anchor_path)}' not found — patch not applied")

        patched_chunk = modified_module.code
        print("[patch-gen] 🧬 Patched chunk generated.")

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
        print(f"[patch-gen] Anchor Path: {anchor_path}")
        print(f"[patch-gen] Chunk Preview:\n{old_code[:300]}...")

        return {
            "patched_code": patched_code,
            "diff": diff,
            "metadata": {
                "insertion_point": " → ".join(anchor_path),
                "change_type": "insert",
                "repo_id": self.context.get("repo_id"),
                "file_path": self.context.get("file_path"),
                "base_sha": self.context.get("base_sha"),
                "anchor_lines": anchor_lines,
                "anchor_path": anchor_path   # ✅ ADD THIS LINE
            }
        }

