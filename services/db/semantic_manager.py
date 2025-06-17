from settings import Database
import json

class SemanticManager:
    def __init__(self):
        self.db = Database().get_connection()

    def resolve_repo_pk(self, logical_repo_id):
        """
        Converts logical repo_id (octocat/Hello-World) to federation_repo.id (PK)
        """
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT id FROM federation_repo WHERE repo_id = %s
            """, (logical_repo_id,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Logical repo_id '{logical_repo_id}' not found in federation_repo")
            return result[0]

    def resolve_repo_logical(self, repo_id):
        """
        Converts federation_repo.id (PK) to logical repo_id (octocat/Hello-World)
        """
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT repo_id FROM federation_repo WHERE id = %s
            """, (repo_id,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Repo ID {repo_id} not found in federation_repo")
            return result[0]

    def save_semantic_node(self, repo_id, node):
        """
        Always expects integer repo_id PK.
        """
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO semantic_node (repo_id, file_path, node_type, name, args, docstring, methods, inherits_from)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                repo_id,
                node.get("file_path"),
                node.get("node_type"),
                node.get("name"),
                json.dumps(node.get("args")),
                node.get("docstring"),
                json.dumps(node.get("methods")),
                node.get("inherits_from")
            ))
