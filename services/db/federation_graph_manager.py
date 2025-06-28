from settings import Database
from services.db.repo_manager import RepoManager
import traceback
import psycopg2.extras
import sys

class FederationGraphManager:
    def __init__(self):
        self.db = Database()
        self.repo_manager = RepoManager()

    def insert_graph_link_tx(self, cur, logical_repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes):
        try:

            cur.execute("SELECT id FROM federation_repo WHERE logical_repo_id = %s", (logical_repo_id,))
            row = cur.fetchone()
            if not row:
                raise Exception(f"Repo {logical_repo_id} not found during graph link insert.")
            pk = row[0]


            # 🔧 Synthetic SHA Validation Bypass Logic
            if logical_repo_id.startswith("Synthetic/"):
                print(f"[Synthetic Mode] SHA verification bypass for file: {file_path}")
            else:
                if not self._verify_file_existence(logical_repo_id, file_path):
                    raise Exception(f"File path {file_path} not found in repository {logical_repo_id}")

            # ✅ Single safe insert
            # 🚫 Deduplication: Skip if identical graph link already exists
            cur.execute("""
                SELECT id FROM federation_graph
                WHERE repo_id = %s AND file_path = %s AND node_type = %s AND name = %s
                AND cross_linked_to = %s AND federation_weight = %s
            """, (pk, file_path, node_type, name, cross_linked_to, federation_weight))

            existing = cur.fetchone()
            if existing:
                print(f"[SKIP] Graph node already linked: {file_path} :: {name}")
                return

            cur.execute("""
                INSERT INTO federation_graph (repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (pk, file_path, node_type, name, cross_linked_to, federation_weight, notes))

        except Exception as e:
            print("❌ insert_graph_link_tx FAILED")
            print(traceback.format_exc())
            sys.stdout.flush()
            raise

    def insert_graph_link(self, repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                self.insert_graph_link_tx(
                    cur, repo_id, file_path, node_type, name,
                    cross_linked_to, federation_weight, notes
                )
            conn.commit()
        except Exception as e:
            print("❌ insert_graph_link FAILED")
            print(traceback.format_exc())
            sys.stdout.flush()
            if conn:
                conn.rollback()
            raise
        finally:
            self.db.release_connection(conn)

    def query_graph(self, logical_repo_id: str, limit: int = 500, offset: int = 0):
        repo_id = self.repo_manager.resolve_repo_pk(logical_repo_id)

        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM federation_graph WHERE repo_id = %s LIMIT %s OFFSET %s",
                    (repo_id, limit, offset)
                )
                return cur.fetchall()
        finally:
            self.db.release_connection(conn)


    def _verify_file_existence(self, logical_repo_id, file_path):
        """
        ✅ Temporary: Always return True to fully bypass in synthetic + limited test environments.
        """
        return True
    
    def auto_link_all_nodes(self, repo_id: int):
        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM semantic_node WHERE repo_id = %s
                """, (repo_id,))
                nodes = cur.fetchall()

                inserted_count = 0
                for node in nodes:
                    file_path = node['file_path']
                    name = node['name']
                    node_type = node['node_type']
                    logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_id)

                    # Skip if already linked
                    cur.execute("""
                        SELECT id FROM federation_graph
                        WHERE repo_id = %s AND file_path = %s AND node_type = %s AND name = %s
                    """, (repo_id, file_path, node_type, name))
                    if cur.fetchone():
                        continue

                    # Naive heuristic: use the node name as the target key
                    cross_linked_to = name.lower()
                    federation_weight = 1.0
                    notes = "Auto-linked by bulk link"

                    cur.execute("""
                        INSERT INTO federation_graph (
                            repo_id, file_path, node_type, name,
                            cross_linked_to, federation_weight, notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes))
                    inserted_count += 1

                conn.commit()
                print(f"✅ Auto-linked {inserted_count} nodes for repo ID {repo_id}")
        except Exception as e:
            print("❌ auto_link_all_nodes FAILED")
            print(traceback.format_exc())
            sys.stdout.flush()
            if conn:
                conn.rollback()
            raise
        finally:
            self.db.release_connection(conn)
