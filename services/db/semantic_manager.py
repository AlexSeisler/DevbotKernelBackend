from settings import Database
import json
from typing import Optional, Dict


class SemanticManager:
    def __init__(self):
        self.db = Database()

    def save_semantic_node(self, repo_pk, node):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO semantic_node (
                        repo_id, file_path, node_type, name, args,
                        docstring, methods, inherits_from,
                        return_type, decorators, code_block, interface_type
                    )
                    VALUES (%s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s)
                    """,
                    (
                        repo_pk,
                        node.get("file_path"),
                        node.get("node_type"),
                        node.get("name"),
                        json.dumps(node.get("args")),
                        node.get("docstring"),
                        json.dumps(node.get("methods")),
                        node.get("inherits_from"),
                        node.get("return_type"),
                        json.dumps(node.get("decorators")),
                        node.get("code_block"),
                        node.get("interface_type"),
                    )
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save semantic node: {str(e)}")
        finally:
            self.db.release_connection(conn)

    def semantic_nodes_exist(self, repo_pk: int, file_path: str) -> bool:
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM semantic_node
                    WHERE repo_id = %s AND file_path = %s
                    """,
                    (repo_pk, file_path)
                )
                count = cur.fetchone()[0]
                return count > 0
        finally:
            self.db.release_connection(conn)
    def get_node_by_key(self, repo_id: int, file_path: str, name: str) -> Optional[Dict]:
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT node_type FROM semantic_node
                    WHERE repo_id = %s AND file_path = %s AND name = %s
                    LIMIT 1
                """, (repo_id, file_path, name))
                row = cur.fetchone()
                if row:
                    return {'node_type': row[0]}
                return None
        finally:
            self.db.release_connection(conn)
