from services.db.federation_graph_manager import FederationGraphManager

class ReplicationPlanBuilder:
    def __init__(self):
        self.graph_manager = FederationGraphManager()

    def build_plan(self, source_repo_id, target_repo_id):
        graph = self.graph_manager.query_graph(source_repo_id)

        modules = []
        for node in graph:
            modules.append({
                "file_path": node["file_path"],
                "node_name": node["name"],
                "linked_to": node["cross_linked_to"],
                "replication_strategy": "direct_import"
            })

        return {
            "source_repo_id": source_repo_id,
            "target_repo_id": target_repo_id,
            "modules": modules,
            "commit_message": f"Replicated modules from {source_repo_id} into {target_repo_id}"
        }
