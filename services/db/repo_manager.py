from settings import Database

class RepoManager:
    def __init__(self):
        self.db = Database().get_connection()

    def save_repo_tx(self, cur, logical_repo_id, branch, root_sha):
        """
        Insert into federation_repo. Always insert logical string repo_id.
        Returns internal DB PK id.
        """
        cur.execute("""
            INSERT INTO federation_repo (repo_id, branch, root_sha)
            VALUES (%s, %s, %s)
            ON CONFLICT (repo_id) DO NOTHING
            RETURNING id;
        """, (logical_repo_id, branch, root_sha))
        result = cur.fetchone()

        if result:
            return result[0]
        else:
            # If already exists, fetch its ID
            cur.execute("SELECT id FROM federation_repo WHERE repo_id = %s", (logical_repo_id,))
            existing = cur.fetchone()
            if existing:
                return existing[0]
            else:
                raise Exception("Failed to insert or retrieve repo.")

    def get_repo_by_repo_id(self, logical_repo_id):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT id, repo_id, branch, root_sha
                FROM federation_repo
                WHERE repo_id = %s
            """, (logical_repo_id,))
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
        Takes either integer (PK) or string (logical repo_id).
        Always resolves to integer PK.
        """
        with self.db.cursor() as cur:
            if isinstance(repo_identifier, int):
                return repo_identifier
            else:
                cur.execute("SELECT id FROM federation_repo WHERE repo_id = %s", (repo_identifier,))
                result = cur.fetchone()
                if not result:
                    raise Exception(f"Repository {repo_identifier} not found.")
                return result[0]

    def resolve_repo_id_by_pk(self, repo_pk_id):
        """
        Reverse lookup PK → logical repo_id string.
        """
        with self.db.cursor() as cur:
            cur.execute("SELECT repo_id FROM federation_repo WHERE id = %s", (repo_pk_id,))
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                return None
