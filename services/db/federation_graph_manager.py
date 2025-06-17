from settings import Database
from services.db.repo_manager import RepoManager

class FederationGraphManager:
    def __init__(self):
        self.db = Database().get_connection()
        self.repo_manager = RepoManager()

    def insert_graph_link_tx(self, cur, logical_repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes):
        pk = self.repo_manager.resolve_repo_pk(logical_repo_id)
        cur.execute("""
            INSERT INTO federation_graph (repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            pk, file_path, node_type, name, cross_linked_to, federation_weight, notes
        ))

    def query_graph(self, logical_repo_id):
        pk = self.repo_manager.resolve_repo_pk(logical_repo_id)
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT file_path, node_type, name, cross_linked_to, federation_weight, notes
                FROM federation_graph WHERE repo_id = %s
            """, (pk,))
            rows = cur.fetchall()
            return [
                {
                    "file_path": r[0],
                    "node_type": r[1],
                    "name": r[2],
                    "cross_linked_to": r[3],
                    "federation_weight": r[4],
                    "notes": r[5]
                }
                for r in rows
            ]
