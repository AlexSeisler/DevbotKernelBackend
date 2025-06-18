from settings import Database
import json

class ProposalManager:
    def __init__(self):
        self.db = Database()

    def save_proposal(self, proposal):
        conn = self.db.get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO patch_proposal (proposal_id, repo_id, branch, proposed_by, commit_message, patches, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    proposal["proposal_id"],
                    proposal["repo_id"],
                    proposal["branch"],
                    proposal["proposed_by"],
                    proposal["commit_message"],
                    json.dumps(proposal["patches"]),
                    proposal["status"]
                ))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save patch proposal: {str(e)}")
        finally:
            self.db.release_connection(conn)

