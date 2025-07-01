from services.db.federation_graph_manager import FederationGraphManager
from services.db.repo_manager import RepoManager

class ReplicationPlanBuilder:
    def __init__(self):
        self.graph_manager = FederationGraphManager()
        self.repo_manager = RepoManager()

    def build_plan(self, source_repo_id, target_repo_id):
        print("[DEBUG] Entered build_plan with:")
        print("  source_repo_id:", source_repo_id, type(source_repo_id))
        print("  target_repo_id:", target_repo_id, type(target_repo_id))

        # 🔒 Normalize numeric IDs from string form
        if isinstance(source_repo_id, str) and source_repo_id.isdigit():
            source_repo_id = int(source_repo_id)
        if isinstance(target_repo_id, str) and target_repo_id.isdigit():
            target_repo_id = int(target_repo_id)

        # 🔄 Convert numeric IDs to slugs
        source_repo_id = self.repo_manager.resolve_repo_id_by_pk(source_repo_id)
        target_repo_id = self.repo_manager.resolve_repo_id_by_pk(target_repo_id)

        print("[DEBUG] Normalized repo_ids:")
        print("  source_repo_id:", source_repo_id)
        print("  target_repo_id:", target_repo_id)

        # Load graphs
        source_graph = self.graph_manager.query_graph(source_repo_id)
        target_graph = self.graph_manager.query_graph(target_repo_id)

        # Construct lookup for target nodes
        target_keys = set((n["file_path"], n["name"]) for n in target_graph)

        seen = set()
        modules = []
        for node in source_graph:
            key = (node["file_path"], node["name"], node["cross_linked_to"])

            # Skip if already exists
            if (node["file_path"], node["name"]) in target_keys:
                print(f"🚫 SKIP: Already exists in target → {node['file_path']} :: {node['name']}")
                continue

            # Tag-aware filter
            tags = set(node.get("tags", []))
            if tags.intersection({"noop", "test", "infra", "skip"}):
                print(f"⚠️ SKIP: Filtered by tag → {node['file_path']} :: {node['name']} :: {tags}")
                continue

            if "entrypoint" not in tags and "service" not in tags:
                print(f"⚠️ SKIP: Non-priority tag set → {node['file_path']} :: {node['name']} :: {tags}")
                continue

            if key not in seen:
                seen.add(key)
                modules.append({
                    "file_path": node["file_path"],
                    "node_name": node["name"],
                    "linked_to": node["cross_linked_to"],
                    "replication_strategy": "direct_import"
                })

        print(f"[PLAN BUILDER] {len(modules)} modules selected from {len(source_graph)} source nodes")

        # ✅ If no modules were selected, return safe empty plan
        if not modules:
            print("[BUILD_PLAN] No modules selected for replication — empty plan")
            return {
                "modules": [],
                "source_repo": source_repo_id,
                "target_repo": target_repo_id
            }

        return {
            "source_repo_id": source_repo_id,
            "target_repo_id": target_repo_id,
            "modules": modules,
            "commit_message": "",
            "target_branch": ""
        }
