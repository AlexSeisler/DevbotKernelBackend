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
        with self.db.get_connection().cursor() as cur:
            cur.execute("SELECT id FROM federation_repo WHERE repo_id = %s", (logical_repo_id,))
            row = cur.fetchone()
            if not row:
                raise Exception(f"Repo {logical_repo_id} not found")
            return row[0]

    def resolve_repo_id_by_pk(self, repo_pk_id):
        with self.db.get_connection().cursor() as cur:
            cur.execute("SELECT repo_id FROM federation_repo WHERE id = %s", (repo_pk_id,))
            row = cur.fetchone()
            if not row:
                raise Exception(f"PK {repo_pk_id} not found")
            return row[0]

