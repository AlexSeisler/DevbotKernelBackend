import libcst as cst
import difflib


class InjectTransformer(cst.CSTTransformer):
    def __init__(self, anchor_name: str, injected_code: str):
        self.anchor_name = anchor_name
        self.injected_code = injected_code
        self.inserted = False

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value == self.anchor_name and not self.inserted:
            new_body = updated_node.body.with_changes(
                body=[
                    cst.parse_statement(self.injected_code)
                ] + updated_node.body.body
            )
            self.inserted = True
            return updated_node.with_changes(body=new_body)
        return updated_node


class FederatedCSTPatchPlanner:
    def __init__(self, context: dict = None):
        self.context = context or {}

    def generate_patch(self, old_code: str, anchor: str, code_block: str) -> dict:
        module = cst.parse_module(old_code)
        transformer = InjectTransformer(anchor_name=anchor, injected_code=code_block)
        modified_module = module.visit(transformer)
        patched_code = modified_module.code

        diff = "\n".join(
            difflib.unified_diff(
                old_code.splitlines(),
                patched_code.splitlines(),
                fromfile=self.context.get("file_path", "before.py"),
                tofile=self.context.get("file_path", "after.py"),
                lineterm=""
            )
        )

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
