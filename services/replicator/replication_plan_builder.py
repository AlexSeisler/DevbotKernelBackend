from services.db.federation_graph_manager import FederationGraphManager
from services.db.repo_manager import RepoManager

class ReplicationPlanBuilder:
    def __init__(self):
        self.graph_manager = FederationGraphManager()
        self.repo_manager = RepoManager()

    def build_plan(self, source_repo_id, target_repo_id):
        # 🔁 Normalize PKs if passed as integers
        source_repo_id = int(source_repo_id) if not isinstance(source_repo_id, int) else source_repo_id
        target_repo_id = int(target_repo_id) if not isinstance(target_repo_id, int) else target_repo_id



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
            "commit_message": "",
            "target_branch": ""
        }