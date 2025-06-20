import os
import time
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, retries=5, delay=2):
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        attempt = 0

        while attempt < retries:
            try:
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=self.dsn
                )
                if self.pool:
                    print("✅ Connection pool established")
                    break
            except psycopg2.OperationalError as e:
                print(f"DB connection pool failed (attempt {attempt+1}): {e}")
                attempt += 1
                time.sleep(delay)

        if not self.pool:
            raise Exception("Database connection pool failed after retries.")

    def get_connection(self):
        return self.pool.getconn()

    def release_connection(self, conn):
        if conn:
            self.pool.putconn(conn)
        else:
            print("⚠️ [POOL] Attempted to release a null connection")

    def close_all(self):
        print("🛑 [POOL] Closing all connections")
        self.pool.closeall()
