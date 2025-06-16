from settings import Database

class RepoManager:
    def __init__(self):
        self.db = Database().get_connection()

    def save_repo_tx(self, cur, repo_id, branch, root_sha):
        cur.execute("""
            INSERT INTO federation_repo (repo_id, branch, root_sha)
            VALUES (%s, %s, %s)
            ON CONFLICT (repo_id) DO NOTHING;
        """, (repo_id, branch, root_sha))
