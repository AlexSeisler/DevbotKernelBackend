from settings import Database

class RepoManager:
    def __init__(self):
        self.db = Database().get_connection()

    def save_repo(self, repo_id, branch, root_sha):
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO federation_repo (repo_id, branch, root_sha)
                VALUES (%s, %s, %s)
                ON CONFLICT (repo_id) DO NOTHING;
            """, (repo_id, branch, root_sha))

    def get_repo_by_repo_id(self, repo_id):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT id, repo_id, branch, root_sha
                FROM federation_repo
                WHERE repo_id = %s
            """, (repo_id,))
            result = cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "repo_id": result[1],
                    "branch": result[2],
                    "root_sha": result[3]
                }
            else:
                return None
    def resolve_repo_id(self, repo_identifier):
        """
        Accepts either an integer (PK) or logical string (octocat/Hello-World).
        Returns internal DB PK.
        """
        with self.db.cursor() as cur:
            if isinstance(repo_identifier, int):
                # Direct PK passthrough
                return repo_identifier
            else:
                # Logical repo_id lookup
                cur.execute("""
                    SELECT id FROM federation_repo WHERE repo_id = %s
                """, (repo_identifier,))
                result = cur.fetchone()
                if not result:
                    raise Exception(f"Repository {repo_identifier} not found in ingestion registry.")
                return result[0]
