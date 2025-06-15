from settings import Database

class FederationGraphManager:
    def __init__(self):
        self.db = Database().get_connection()

    def insert_graph_link(self, repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes):
        with self.db.cursor() as cur:
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

            # Convert query output into list of dicts
            graph = []
            for row in results:
                graph.append({
                    "repo_id": row[0],
                    "file_path": row[1],
                    "node_type": row[2],
                    "name": row[3],
                    "cross_linked_to": row[4],
                    "federation_weight": row[5],
                    "notes": row[6]
                })
            return graph
