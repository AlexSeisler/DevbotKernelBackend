"""
tagger.py — Subsystem tagging orchestrator

Handles orchestration of tagging for semantic nodes by:
- Loading subsystem tagging rules from `tag_rules.py`
- Running scoring functions from `confidence.py`
- Normalizing and returning subsystem predictions

This is the refactored replacement for the original `tagging_hook.py`
to enable modular tuning and testing.
"""

from .tag_rules import get_subsystem_map
from .confidence import aggregate_scores


class Tagger:
    def __init__(self):
        self.subsystem_map = get_subsystem_map()

    def _normalize_subsystems(self, subsystems):
        """
        Normalize subsystem names by making them lowercase and deduplicating.
        """
        if not subsystems:
            return []
        normalized = list({s.lower().strip() for s in subsystems if s})
        return normalized

    def infer_subsystem(self, file_path, imports, decorators, content_lines):
        """
        Infer subsystems for a given semantic node using modular scoring.
        """
        subsystems = aggregate_scores(
            self.subsystem_map,
            file_path,
            file_path.split("/")[-1],  # filename
            imports,
            decorators,
            content_lines
        )

        if not subsystems:
            return ["core"]

        normalized = self._normalize_subsystems(subsystems)
        return normalized or ["core"]

    def _tag_semantic_node(self, node):
        """
        Tag a single semantic node with subsystem(s) and secondary classification tags.
        """
        tags = []

        name = node.get("name", "")
        node_type = node.get("node_type", "")
        decorators = node.get("decorators", [])
        file_path = node.get("file_path", "")

        # Restore original secondary tagging logic
        if "test" in file_path:
            tags.append("test")
        if "infra" in file_path or "ops" in file_path:
            tags.append("infra")
        if node_type == "decorator":
            tags.append("decorator")
        if name in {"main", "__init__", "run"}:
            tags.append("entrypoint")
        if name.startswith("_"):
            tags.append("internal")
        if any(k in d for d in decorators for k in ("get", "post", "route")):
            tags.append("http")
        if not tags:
            tags.append("util")

        # Assign subsystem predictions
        imports = node.get("imports", [])
        content_lines = node.get("content", "").split("\n") if node.get("content") else []
        node["subsystems"] = self.infer_subsystem(file_path, imports, decorators, content_lines)
        node["tags"] = tags
        return node

    def _tag_all_semantic_nodes(self, nodes):
        """
        Apply tagging to all semantic nodes in a list, grouped by file for subsystem inference.
        """
        from collections import defaultdict
        file_groups = defaultdict(list)
        for node in nodes:
            file_groups[node["file_path"]].append(node)

        for file_path, group in file_groups.items():
            imports = set()
            decorators = set()
            lines = []
            for node in group:
                imports.update(node.get("imports", []))
                decorators.update(node.get("decorators", []))
                lines.extend(node.get("source_code", "").splitlines())

            subsystems = self.infer_subsystem(file_path, list(imports), list(decorators), lines)
            for node in group:
                node["subsystems"] = subsystems
                self._tag_semantic_node(node)

        return nodes
