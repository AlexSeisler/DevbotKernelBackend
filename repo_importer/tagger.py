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
        Tag a single semantic node with subsystem(s).
        """
        file_path = node.get("file_path", "")
        imports = node.get("imports", [])
        decorators = node.get("decorators", [])
        content_lines = node.get("content", "").split("\n") if node.get("content") else []

        node["subsystems"] = self.infer_subsystem(file_path, imports, decorators, content_lines)
        return node

    def _tag_all_semantic_nodes(self, nodes):
        """
        Apply tagging to all semantic nodes in a list.
        """
        return [self._tag_semantic_node(node) for node in nodes]