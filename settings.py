import psycopg2
import os

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("FEDERATION_DB_NAME"),
            user=os.getenv("FEDERATION_DB_USER"),
            password=os.getenv("FEDERATION_DB_PASSWORD"),
            host=os.getenv("FEDERATION_DB_HOST"),
            port=os.getenv("FEDERATION_DB_PORT"),
            sslmode='require'   # ✅ <-- This line is the fix
        )

    def get_connection(self):
        return self.conn
