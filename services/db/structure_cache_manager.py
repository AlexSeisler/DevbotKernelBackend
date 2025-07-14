import psycopg2.extras
from datetime import datetime

class StructureCacheManager:
    def __init__(self, db):
        self.db = db

    def delete_structure_cache(self, repo_id, file_path, branch, sha):
        conn = self.db.get_connection()
        try:
            print(f"[cache] 🗑 Attempting to delete cache for: {repo_id}, {file_path}, {branch}, {sha}")
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM file_structure_cache
                    WHERE repo_id = %s
                    AND file_path = %s
                    AND branch = %s
                    AND sha = %s
                """, (repo_id, file_path, branch, sha))
                print(f"[cache] ✅ Delete executed — {cur.rowcount} rows removed")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[cache] ❌ Delete failed: {e}")
            raise
        finally:
            self.db.release_connection(conn)

    def insert_structure_rows(self, rows):
        if not rows:
            return
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, """
                    INSERT INTO file_structure_cache (
                        repo_id, branch, file_path, sha,
                        anchor_path, anchor_name, anchor_type,
                        start_line, end_line, created_at
                    ) VALUES (
                        %(repo_id)s, %(branch)s, %(file_path)s, %(sha)s,
                        %(anchor_path)s, %(anchor_name)s, %(anchor_type)s,
                        %(start_line)s, %(end_line)s, %(created_at)s
                    )
                """, rows)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.db.release_connection(conn)
