# PATCH — federation_patch_planner.py
import libcst as cst
import difflib
from typing import Optional
import textwrap
import json

class InjectTransformer(cst.CSTTransformer):
    def __init__(self, anchor_path: list, injected_code: str):
        self.anchor_path = anchor_path
        self.injected_code = injected_code
        self.inserted = False
        self.current_path = []
        self.nesting_level = 0
        print(f"[init] 🚀 Initialized InjectTransformer")
        print(f"[init] 📍 anchor_path: {self.anchor_path}")
        print(f"[init] 💉 injected_code:\n{self.injected_code.strip()}")

    def _inject_into_body(self, body: cst.BaseSuite) -> cst.BaseSuite:
        print(f"[inject] 🧾 Original injected_code:\n{self.injected_code!r}")

        try:
            # Parse without any indentation — LibCST handles placement inside the block
            injected_nodes = cst.parse_module(self.injected_code.strip()).body
            print(f"[inject] ✅ Parsed {len(injected_nodes)} node(s)")
        except Exception as e:
            print(f"[inject] ❌ Parsing failed with exception: {e}")
            raise ValueError(f"[transform] ❌ Failed to parse injected code block:\n{self.injected_code}\nError: {e}")

        if isinstance(body, cst.IndentedBlock):
            print(f"[inject] ➕ Appending to existing IndentedBlock (nest={self.nesting_level})")
            return body.with_changes(body=tuple(injected_nodes) + tuple(body.body))
        elif isinstance(body, cst.SimpleStatementSuite):
            print(f"[inject] 🔁 Wrapping new IndentedBlock from SimpleStatementSuite")
            return cst.IndentedBlock(body=list(injected_nodes) + list(body.body))
        else:
            raise ValueError(f"[transform] ❌ Unsupported block type: {type(body)}")

    def _check_and_inject(self, updated_node, body: Optional[cst.BaseSuite]):
        print(f"[check] 🔍 Checking node at path: {self.current_path}")
        print(f"[check] 📏 Matching: expected={self.anchor_path} actual={self.current_path}")

        if self.current_path == self.anchor_path and not self.inserted:
            print(f"[check] 🎯 Anchor match! Inserting into: {' → '.join(self.current_path)}")
            self.nesting_level = len(self.anchor_path)
            if not body:
                raise ValueError(f"[inject] ❌ Cannot inject — no body at anchor path")

            try:
                print(f"[inject] 💥 Injection Triggered — Nesting Level: {self.nesting_level}")
                new_body = self._inject_into_body(body)
                self.inserted = True
                return updated_node.with_changes(body=new_body)
            except Exception as e:
                raise ValueError(f"[inject] ❌ Injection failed: {e}")
        else:
            print(f"[check] ⏭️ No match for path: {' → '.join(self.current_path)}")

        return updated_node

    def visit_ClassDef(self, node: cst.ClassDef):
        print(f"[visit] ➕ ClassDef: {node.name.value}")
        self.current_path.append(node.name.value)

    def leave_ClassDef(self, original_node, updated_node):
        result = self._check_and_inject(updated_node, updated_node.body)
        self.current_path.pop()
        return result

    def visit_FunctionDef(self, node: cst.FunctionDef):
        print(f"[visit] ➕ FunctionDef: {node.name.value}")
        self.current_path.append(node.name.value)

    def leave_FunctionDef(self, original_node, updated_node):
        result = self._check_and_inject(updated_node, updated_node.body)
        self.current_path.pop()
        return result

    def leave_Module(self, original_node, updated_node):
        print(f"[module] 📦 leave_Module — anchor_path: {self.anchor_path}")
        try:
            injected_nodes = tuple(cst.parse_module(self.injected_code.strip()).body)
        except Exception as e:
            raise ValueError(f"[module] ❌ Failed to parse injected code at module level: {e}")

        if self.anchor_path == ["BOF"] and not self.inserted:
            try:
                print(f"[module] ✨ Injecting at BOF")
                self.inserted = True
                return updated_node.with_changes(body=injected_nodes + updated_node.body)
            except Exception as e:
                raise ValueError(f"[module] ❌ BOF injection failed: {e}")

        elif self.anchor_path == ["EOF"] and not self.inserted:
            try:
                print(f"[module] ✨ Injecting at EOF")
                self.inserted = True
                return updated_node.with_changes(body=updated_node.body + injected_nodes)
            except Exception as e:
                raise ValueError(f"[module] ❌ EOF injection failed: {e}")

        print(f"[module] 🧩 No module-level injection performed")
        return updated_node



class FederatedCSTPatchPlanner:
    def __init__(self, context: dict = None):
        self.context = context or {}
        print(f"[planner:init] ⚙️ Context initialized:\n{json.dumps(self.context, indent=2)}")

    def generate_patch(self, old_code: str, anchor: str, code_block: str, patch_strategy: Optional[str] = "insert") -> dict:
        print("[patch-gen] 🔍 Starting generate_patch")
        old_lines = old_code.splitlines()
        anchor_lines = self.context.get("anchor_lines")
        anchor_path = self.context.get("anchor_path", [anchor])

        print(f"[patch-gen] 📌 anchor: {anchor}")
        print(f"[patch-gen] 📍 anchor_path: {anchor_path}")
        print(f"[patch-gen] 📐 anchor_lines: {anchor_lines}")
        print(f"[patch-gen] 🛠 strategy: {patch_strategy}")
        print(f"[patch-gen] 📄 old_code line count: {len(old_lines)}")

        # === Line-level replacement/delete mode
        if patch_strategy in ("replace", "delete") and anchor_lines:
            start, end = anchor_lines
            print(f"[patch-gen] 🔪 Performing line-level {patch_strategy} from {start} to {end}")
            if patch_strategy == "replace":
                new_code_lines = old_lines[:start - 1] + code_block.splitlines() + old_lines[end:]
            else:  # delete
                new_code_lines = old_lines[:start - 1] + old_lines[end:]
            patched_code = "\n".join(new_code_lines)

        elif patch_strategy == "replace" and not anchor_lines:
            print("[patch-gen] ⚠️ 'replace' without anchor_lines — forcing AST-safe insert (non-destructive)")
            patch_strategy = "insert"
            # Fall through to AST injection below

        # === AST-based strategy (insert/append/default)
        if patch_strategy in ("insert", "append"):
            print("[patch-gen] 🧪 Parsing original source with LibCST")
            try:
                module = cst.parse_module(old_code)
            except Exception as e:
                raise ValueError(f"[patch-gen] ❌ Failed to parse original source: {e}")

            print("[patch-gen] 🧬 Instantiating InjectTransformer")
            transformer = InjectTransformer(anchor_path=anchor_path, injected_code=code_block)

            if patch_strategy == "insert":
                transformer._inject_into_body = transformer._inject_into_body
            elif patch_strategy == "append":
                transformer._inject_into_body = lambda body: body.with_changes(
                    body=tuple(body.body) + tuple(cst.parse_module(code_block.strip()).body)
                )

            print("[patch-gen] 🔁 Visiting original module with transformer")
            modified_module = module.visit(transformer)

            if not transformer.inserted:
                raise ValueError(f"[patch-gen] ❌ Anchor path '{' → '.join(anchor_path)}' not found — patch not applied")

            patched_code = modified_module.code


        print("[patch-gen] ✅ Patch injected successfully")
        print("[patch-gen] 📊 Calculating diff")

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

        metadata = {
            "insertion_point": " → ".join(anchor_path),
            "change_type": patch_strategy,
            "repo_id": self.context.get("repo_id"),
            "file_path": self.context.get("file_path"),
            "base_sha": self.context.get("base_sha"),
            "anchor_lines": anchor_lines,
            "anchor_path": anchor_path
        }

        print(f"[patch-gen] 🧠 Metadata:\n{json.dumps(metadata, indent=2)}")

        return {
            "patched_code": patched_code,
            "diff": "\n".join(diff_lines),
            "metadata": metadata
        }
