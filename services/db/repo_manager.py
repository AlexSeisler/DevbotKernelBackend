from settings import Database
from models.federation_models import FederationRepo

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
    def get_slug_by_id(self, repo_id: int) -> str:
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT owner, repo FROM federation_repo WHERE id = %s", (repo_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise Exception(f"Repo with ID {repo_id} not found.")
                return f"{row[0]}/{row[1]}"
        finally:
            self.db.release_connection(conn)
    def insert_or_update_repo(self, repo_id, owner, repo, branch, root_sha):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO federation_repo (repo_id, owner, repo, branch, root_sha)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (repo_id) DO UPDATE SET
                        owner = EXCLUDED.owner,
                        repo = EXCLUDED.repo,
                        branch = EXCLUDED.branch,
                        root_sha = EXCLUDED.root_sha
                """, (repo_id, owner, repo, branch, root_sha))
                conn.commit()
        finally:
            self.db.release_connection(conn)
    
