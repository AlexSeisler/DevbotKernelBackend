import traceback
import json
from uuid import uuid4
from datetime import datetime
import psycopg2.extras


class ProposalManager:
    def __init__(self, db):
        self.db = db

    def save_patch_proposal(self, payload: dict):
        conn = self.db.get_connection()
        proposal_id = str(uuid4())  # Generate once and reuse
        try:
            with conn.cursor() as cur:
                for patch in payload.get("patches", []):
                    cur.execute("""
                        INSERT INTO patch_proposal (
                            proposal_id, repo_id, branch, file_path, base_sha,
                            anchor, code_block, patched_code, diff,
                            metadata, proposed_by, commit_message,
                            status, risk_class, diff_summary, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        proposal_id,
                        payload["repo_id"],
                        payload["branch"],
                        patch["file_path"],
                        patch["base_sha"],
                        patch["anchor"],
                        patch["code_block"],
                        patch["patched_code"],
                        patch["diff"],
                        json.dumps(patch.get("metadata", {})),
                        payload.get("proposed_by", "devbot"),
                        payload.get("commit_message", "Federated patch proposal"),
                        "pending",
                        "UNKNOWN",
                        None,
                        datetime.utcnow()
                    ))

            conn.commit()
            return proposal_id  # ✅ Return the consistent ID
        except Exception as e:
            print("❌ save_patch_proposal FAILED")
            print(traceback.format_exc())
            if conn:
                conn.rollback()
            raise
        finally:
            self.db.release_connection(conn)


    def get_all_proposals(self, repo_id: int):
        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM patch_proposal
                    WHERE repo_id = %s
                    ORDER BY created_at DESC
                """, (repo_id,))
                return cur.fetchall()
        finally:
            self.db.release_connection(conn)
    def update_patch_status(self, patch_id: str, new_status: str):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE patch_proposal
                    SET status = %s
                    WHERE proposal_id = %s
                """, (new_status, patch_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.db.release_connection(conn)
