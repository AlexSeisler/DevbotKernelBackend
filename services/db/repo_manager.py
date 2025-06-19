from settings import Database

class RepoManager:
    def __init__(self):
        self.db = Database()

    def save_repo_tx(self, cur, logical_repo_id, branch, root_sha):
        cur.execute("""
            INSERT INTO federation_repo (repo_id, branch, root_sha)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (logical_repo_id, branch, root_sha))
        return cur.fetchone()[0]

    def resolve_repo_pk(self, logical_repo_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM federation_repo WHERE repo_id = %s", (logical_repo_id,))
                row = cur.fetchone()
                if not row:
                    raise Exception(f"Repo {logical_repo_id} not found")
                return row[0]
        except Exception as e:
            raise e
        finally:
            self.db.release_connection(conn)

    def resolve_repo_id_by_pk(self, repo_pk_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT repo_id FROM federation_repo WHERE id = %s", (repo_pk_id,))
                row = cur.fetchone()
                if not row:
                    raise Exception(f"PK {repo_pk_id} not found")
                return row[0]
        except Exception as e:
            raise e
        finally:
            self.db.release_connection(conn)

    def try_resolve_pk(self, logical_repo_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM federation_repo WHERE repo_id = %s", (logical_repo_id,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            raise e
        finally:
            self.db.release_connection(conn)
