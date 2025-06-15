import os
import psycopg2

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("FEDERATION_DB_NAME"),
            user=os.getenv("FEDERATION_DB_USER"),
            password=os.getenv("FEDERATION_DB_PASSWORD"),
            host=os.getenv("FEDERATION_DB_HOST"),
            port=os.getenv("FEDERATION_DB_PORT")
        )
        self.conn.autocommit = True

    def get_connection(self):
        return self.conn
