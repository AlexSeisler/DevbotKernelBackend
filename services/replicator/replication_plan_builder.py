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

    # Normalize repo_id inputs
        if isinstance(source_repo_id, str):
            source_repo_id = self.repo_manager.resolve_repo_id_by_pk(source_repo_id)

        if isinstance(target_repo_id, str):
            target_repo_id = self.repo_manager.resolve_repo_id_by_pk(target_repo_id)
        print("[DEBUG] Entered build_plan with2:")
        print("  source_repo_id:", source_repo_id, type(source_repo_id))
        print("  target_repo_id:", target_repo_id, type(target_repo_id))

        # Load graphs for both source and target
        source_graph = self.graph_manager.query_graph(source_repo_id)
        target_graph = self.graph_manager.query_graph(target_repo_id)
        print("[DEBUG] Entered build_plan with3:")
        print("  source_repo_id:", source_repo_id, type(source_repo_id))
        print("  target_repo_id:", target_repo_id, type(target_repo_id))

        # ✅ Optimization: Build fast-lookup set for target repo
        target_keys = set(
            (node["file_path"], node["name"])
            for node in target_graph
        )

        seen = set()
        modules = []
        for node in source_graph:
            key = (node["file_path"], node["name"], node["cross_linked_to"])

            # Skip if same structure already exists in target
            if (node["file_path"], node["name"]) in target_keys:
                print(f"🔁 SKIP: Already exists in target — {node['file_path']} :: {node['name']}")
                continue

            if key not in seen:
                seen.add(key)
                modules.append({
                    "file_path": node["file_path"],
                    "node_name": node["name"],
                    "linked_to": node["cross_linked_to"],
                    "replication_strategy": "direct_import"
                })

        print(f"[PLAN BUILDER] Generated {len(modules)} unique modules from {len(source_graph)} source nodes")

        return {
            "source_repo_id": source_repo_id,
            "target_repo_id": target_repo_id,
            "modules": modules,
            "commit_message": "",
            "target_branch": ""
        }
