from settings import Database
from services.db.repo_manager import RepoManager  # 🔧 import for bidirectional repo_id mapping

class FederationGraphManager:
    def __init__(self):
        self.db = Database().get_connection()
        self.repo_manager = RepoManager()  # 🔧 instantiate repo resolver

    def insert_graph_link_tx(self, cur, repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes):
        cur.execute("""
            INSERT INTO federation_graph (repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            repo_id,
            file_path,
            node_type,
            name,
            cross_linked_to,
            federation_weight,
            notes
        ))

    def query_graph(self, repo_id=None):
        with self.db.cursor() as cur:
            if repo_id:
                cur.execute("""
                    SELECT repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes
                    FROM federation_graph
                    WHERE repo_id = %s
                """, (repo_id,))
            else:
                cur.execute("""
                    SELECT repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes
                    FROM federation_graph
                """)
            results = cur.fetchall()

            graph = []
            for row in results:
                pk_repo_id = row[0]
                logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(pk_repo_id)
                graph.append({
                    "repo_id": logical_repo_id,  # ✅ PATCHED: return logical repo_id string
                    "file_path": row[1],
                    "node_type": row[2],
                    "name": row[3],
                    "cross_linked_to": row[4],
                    "federation_weight": row[5],
                    "notes": row[6]
                })
            return graph
