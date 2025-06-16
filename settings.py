import psycopg2
import os

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dsn=os.getenv("DATABASE_URL"),
            sslmode='require'
        )

    def get_connection(self):
        return self.conn
