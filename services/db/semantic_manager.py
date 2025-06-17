from settings import Database
import json
from services.db.repo_manager import RepoManager  # 🔧 Use repo resolver for full ID consistency

class SemanticManager:
    def __init__(self):
        self.db = Database().get_connection()
        self.repo_manager = RepoManager()

    def resolve_repo_pk(self, logical_repo_id):
        """
        Converts logical repo_id (octocat/Hello-World) to federation_repo.id (PK)
        """
        return self.repo_manager.resolve_repo_id(logical_repo_id)

    def resolve_repo_logical(self, repo_id):
        """
        Converts federation_repo.id (PK) to logical repo_id (octocat/Hello-World)
        """
        return self.repo_manager.resolve_repo_id_by_pk(repo_id)

    def save_semantic_node(self, logical_or_pk_repo_id, node):
        """
        Accepts either logical string or integer repo_id. Always resolves to PK before insertion.
        """
        # Normalize input to PK ID
        if isinstance(logical_or_pk_repo_id, int):
            repo_pk = logical_or_pk_repo_id
        else:
            repo_pk = self.repo_manager.resolve_repo_id(logical_or_pk_repo_id)

        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO semantic_node (repo_id, file_path, node_type, name, args, docstring, methods, inherits_from)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                repo_pk,
                node.get("file_path"),
                node.get("node_type"),
                node.get("name"),
                json.dumps(node.get("args")),
                node.get("docstring"),
                json.dumps(node.get("methods")),
                node.get("inherits_from")
            ))
