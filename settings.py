import psycopg2
from psycopg2 import pool
import os
import time
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, retries=5, delay=2):
        dsn = os.getenv("DATABASE_URL")
        attempt = 0
        self.pool = None

        while attempt < retries:
            try:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=dsn
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
        try:
            return self.pool.getconn()
        except Exception as e:
            raise Exception("Failed to retrieve connection from pool") from e

    def release_connection(self, conn):
        if self.pool and conn:
            self.pool.putconn(conn)

    def close_all(self):
        if self.pool:
            self.pool.closeall()
