from settings import Database
import json

class SemanticManager:
    def __init__(self):
        self.db = Database().get_connection()

    def resolve_repo_id(self, repo_id):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT repo_id FROM federation_repo WHERE id = %s
            """, (repo_id,))
            result = cur.fetchone()
            if not result:
                raise Exception(f"Repo ID {repo_id} not found in federation_repo")
            return result[0]  # returns 'octocat/Hello-World'

    def save_semantic_node(self, repo_id, node):
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
