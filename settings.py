import psycopg2
import os
import time

class Database:
    def __init__(self, retries=5, delay=2):
        dsn = os.getenv("DATABASE_URL")
        attempt = 0
        while attempt < retries:
            try:
                self.conn = psycopg2.connect(
                    dsn=dsn,
                    connect_timeout=10
                )
                break  # success
            except psycopg2.OperationalError as e:
                print(f"DB connection failed (attempt {attempt+1}): {e}")
                attempt += 1
                time.sleep(delay)
        else:
            raise Exception("Database connection failed after retries.")

    def get_connection(self):
        return self.conn
