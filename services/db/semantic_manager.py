from settings import Database
import json

class SemanticManager:
    def __init__(self):
        self.db = Database().get_connection()

    def save_semantic_node(self, repo_pk, node):
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
