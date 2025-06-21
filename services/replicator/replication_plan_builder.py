from services.db.federation_graph_manager import FederationGraphManager
from services.db.repo_manager import RepoManager

class ReplicationPlanBuilder:
    def __init__(self):
        self.graph_manager = FederationGraphManager()
        self.repo_manager = RepoManager()

    def build_plan(self, source_repo_id, target_repo_id):
        # 🔁 If passed as integers, resolve to logical repo_id strings
        if isinstance(source_repo_id, int):
            source_repo_id = self.repo_manager.resolve_repo_id_by_pk(source_repo_id)
        if isinstance(target_repo_id, int):
            target_repo_id = self.repo_manager.resolve_repo_id_by_pk(target_repo_id)

        graph = self.graph_manager.query_graph(source_repo_id)

        seen = set()
        modules = []
        for node in graph:
            key = (node["file_path"], node["name"], node["cross_linked_to"])
            if key not in seen:
                seen.add(key)
                modules.append({
                    "file_path": node["file_path"],
                    "node_name": node["name"],
                    "linked_to": node["cross_linked_to"],
                    "replication_strategy": "direct_import"
                })

        print(f"[PLAN BUILDER] Generated {len(modules)} unique modules from {len(graph)} graph nodes")

        return {
            "source_repo_id": source_repo_id,
            "target_repo_id": target_repo_id,
            "modules": modules,
            "commit_message": "",
            "target_branch": ""
        }
