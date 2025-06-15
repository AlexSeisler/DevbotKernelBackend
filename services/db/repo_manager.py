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
