from psycopg2 import sql
from settings import Database

db = Database()
ALLOWED_TABLES = {"file_structure_cache"}

def execute_query(db, table, filters, limit=100, order_by=None, desc=False):
    print("[/query] 📥 Incoming query")
    print(f"Table: {table}")
    print(f"Filters: {filters}")
    print(f"Limit: {limit}, Order by: {order_by}, Desc: {desc}")

    if table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    conn = db.get_connection()
    try:
        base = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
        clauses = []
        values = []

        for key, val in filters.items():
            if isinstance(val, list):
                # Use Postgres array containment check
                clauses.append(sql.SQL("{} @> %s").format(sql.Identifier(key)))
            else:
                clauses.append(sql.SQL("{} = %s").format(sql.Identifier(key)))
            values.append(val)

        where = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(clauses) if clauses else sql.SQL("")

        order = sql.SQL("")
        if order_by:
            order = sql.SQL(" ORDER BY {} {}").format(
                sql.Identifier(order_by),
                sql.SQL("DESC") if desc else sql.SQL("ASC")
            )

        full_query = base + where + order + sql.SQL(" LIMIT %s")
        values.append(limit)

        print(f"SQL: {full_query.as_string(conn)}")
        print(f"Values: {values}")

        with conn.cursor() as cur:
            cur.execute(full_query, values)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]

    finally:
        db.release_connection(conn)
