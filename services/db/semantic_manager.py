from settings import Database
import json

class SemanticManager:
    def __init__(self):
        self.db = Database()

    def save_semantic_node(self, repo_pk, node):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
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
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save semantic node: {str(e)}")
        finally:
            self.db.release_connection(conn)
