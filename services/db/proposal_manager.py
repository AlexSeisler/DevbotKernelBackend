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
                    INSERT INTO patch_proposal (
                        proposal_id, repo_id, branch, proposed_by,
                        commit_message, patches, status, risk_class, diff_summary
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

                """, (
                    proposal["proposal_id"],
                    proposal["repo_id"],
                    proposal["branch"],
                    proposal["proposed_by"],
                    proposal["commit_message"],
                    json.dumps(proposal["patches"]),
                    proposal["status"],
                    proposal.get("risk_class", "UNKNOWN"),
                    proposal.get("diff_summary", "")
                ))
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save patch proposal: {str(e)}")
        finally:
            self.db.release_connection(conn)
    def get_pending_proposals(self, risk_class_whitelist):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT proposal_id, repo_id, branch, proposed_by, commit_message, patches, status, risk_class
                    FROM patch_proposal
                    WHERE status = 'pending'
                    AND risk_class = ANY(%s)
                """, (risk_class_whitelist,))
                rows = cur.fetchall()
                return [
                    {
                        "proposal_id": row[0],
                        "repo_id": row[1],
                        "branch": row[2],
                        "proposed_by": row[3],
                        "commit_message": row[4],
                        "patches": row[5] if isinstance(row[5], list) else json.loads(row[5]),
                        "status": row[6],
                        "risk_class": row[7]
                    }
                    for row in rows
                ]
        finally:
            self.db.release_connection(conn)


    def mark_proposal_committed(self, proposal_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE patch_proposal
                    SET status = 'committed'
                    WHERE proposal_id = %s
                """, (proposal_id,))
                conn.commit()
        finally:
            self.db.release_connection(conn)
