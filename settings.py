import os
import time
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, retries=5, delay=2):
        self.dsn = os.getenv('DATABASE_URL')
        self.pool = None
        attempt = 0

        while attempt < retries:
            try:
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=2,  # 🔧 Supabase Free Tier Safe
                    dsn=self.dsn
                )
                if self.pool:
                    print(f"✅ DB connection pool established (attempt {attempt + 1})")
                    break
            except psycopg2.OperationalError as e:
                print(f"❌ DB connection pool failed (attempt {attempt + 1}): {e}")
                attempt += 1
                time.sleep(delay)

        if not self.pool:
            raise Exception("❌ Database connection pool failed after retries.")

    def get_connection(self):
        try:
            return self.pool.getconn()
        except Exception as e:
            print(f"⚠️ Failed to get connection from pool: {e}")
            return None

    def release_connection(self, conn):
        if conn:
            try:
                self.pool.putconn(conn)
            except Exception as e:
                print(f"⚠️ Failed to release connection: {e}")
        else:
            print("⚠️ [POOL] Attempted to release a null connection")

    def close_all(self):
        print("🛑 [POOL] Closing all connections")
        self.pool.closeall()
