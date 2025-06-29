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
                cur.execute("SELECT id FROM federation_repo WHERE logical_repo_id = %s", (logical_repo_id,))
                row = cur.fetchone()
                if not row:
                    raise Exception(f"Repo {logical_repo_id} not found")
                return row[0]
        finally:
            self.db.release_connection(conn)


    def resolve_repo_id_by_pk(self, repo_pk_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT owner, repo FROM federation_repo WHERE id = %s", (repo_pk_id,))
                row = cur.fetchone()
                if not row:
                    raise Exception(f"PK {repo_pk_id} not found")
                return f"{row[0]}/{row[1]}"
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
        print(f"[TRACE] get_slug_by_id() called with repo_id: {repo_id} ({type(repo_id)})")

        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT owner, repo FROM federation_repo WHERE id = %s", (repo_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise Exception(f"Repo with ID {repo_id} not found.")
                print(f"[SLUG LOOKUP] Loaded owner/repo = {row}")

                return f"{row[0]}/{row[1]}"
        finally:
            self.db.release_connection(conn)
            
    def get_repo_by_slug(self, slug: str) -> int:
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM federation_repo WHERE logical_repo_id = %s", (slug,)
                )

                row = cur.fetchone()
                if not row:
                    raise Exception(f"Repo with slug {slug} not found.")
                return row[0]
        finally:
            self.db.release_connection(conn)

    def insert_or_update_repo(self, repo_id, owner, repo, branch, root_sha):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                name = repo
                logical_repo_id = f"{owner}/{repo}"
                cur.execute("""
                    INSERT INTO federation_repo (repo_id, owner, repo, name, logical_repo_id, branch, root_sha, ingestion_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (repo_id) DO UPDATE SET
                        owner = EXCLUDED.owner,
                        repo = EXCLUDED.repo,
                        name = EXCLUDED.name,
                        logical_repo_id = EXCLUDED.logical_repo_id,
                        branch = EXCLUDED.branch,
                        root_sha = EXCLUDED.root_sha,
                        ingestion_date = CURRENT_TIMESTAMP
                    RETURNING id
                """, (repo_id, owner, repo, name, logical_repo_id, branch, root_sha))
                conn.commit()
                row = cur.fetchone()
                

                return row[0]
        finally:
            self.db.release_connection(conn)


    def get_last_analysis_record(self, repo_id, branch):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT sha, node_count
                    FROM analysis_record
                    WHERE repo_id = %s AND branch = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (repo_id, branch))
                row = cur.fetchone()
                return {"sha": row[0], "node_count": row[1]} if row else None
        finally:
            self.db.release_connection(conn)
    def record_analysis(self, repo_id, sha, node_count):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_record (repo_id, sha, node_count, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (repo_id, sha, node_count))
                conn.commit()
        finally:
            self.db.release_connection(conn)
