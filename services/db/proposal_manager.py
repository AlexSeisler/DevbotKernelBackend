from settings import Database
import json

class ProposalManager:
    def __init__(self):
        self.db = Database()

    def save_proposal(self, proposal):
        if not proposal.get("patches"):
            raise Exception("Empty patch cannot be saved.")

        if not isinstance(proposal["patches"], list) or not proposal["patches"][0].get("updated_content"):
            raise Exception("Patch must contain updated_content.")

        if proposal.get("risk_class") in (None, "", "UNKNOWN"):
            raise Exception("Risk classification must be explicitly set before saving.")

        # Normalize updated_content
        for patch in proposal["patches"]:
            if "updated_content" in patch:
                patch["updated_content"] = patch["updated_content"].strip()

        # Optional: inject basic diff summary if missing
        if "diff_summary" not in proposal or not proposal.get("diff_summary"):
            proposal["diff_summary"] = f"Patches: {len(proposal['patches'])}, Risk: {proposal.get('risk_class', 'UNKNOWN')}"

        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO patch_proposal (
                        proposal_id, repo_id, branch, proposed_by,
                        commit_message, patches, status, risk_class, diff_summary
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        proposal["proposal_id"],
                        proposal["repo_id"],
                        proposal["branch"],
                        proposal["proposed_by"],
                        proposal["commit_message"],
                        json.dumps(proposal["patches"]),
                        proposal["status"],
                        proposal["risk_class"],
                        proposal["diff_summary"]
                    )
                )
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
    def get_proposal_by_id(self, proposal_id):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT proposal_id, repo_id, branch, proposed_by,
                        commit_message, patches, status, risk_class, diff_summary
                    FROM patch_proposal
                    WHERE proposal_id = %s
                """, (proposal_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "proposal_id": row[0],
                    "repo_id": row[1],
                    "branch": row[2],
                    "proposed_by": row[3],
                    "commit_message": row[4],
                    "patches": json.loads(row[5]) if isinstance(row[5], str) else row[5],
                    "status": row[6],
                    "risk_class": row[7],
                    "diff_summary": row[8]
                }
        finally:
            self.db.release_connection(conn)
