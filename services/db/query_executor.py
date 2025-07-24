from psycopg2 import sql
from settings import _db_instance

db = _db_instance


def execute_query(db, table, filters, limit=100, order_by=None, desc=False):
    print("[/query] 📥 Incoming query")
    print(f"Table: {table}")
    print(f"Filters: {filters}")
    print(f"Limit: {limit}, Order by: {order_by}, Desc: {desc}")

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
def insert_rows(table, rows):
    if not rows:
        return []

    columns = rows[0].keys()
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() * len(columns))
    )

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            inserted = []
            for row in rows:
                values = [row[col] for col in columns]
                cur.execute(query.as_string(conn), values)
                inserted_row = cur.fetchone()
                column_names = [desc[0] for desc in cur.description]
                inserted.append(dict(zip(column_names, inserted_row)))
            conn.commit()
            return inserted
    finally:
        db.release_connection(conn)


def update_rows(table, filters, updates):
    set_clause = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in updates]
    where_clause = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in filters]
    values = list(updates.values()) + list(filters.values())

    query = sql.SQL("UPDATE {} SET {} WHERE {} RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(", ").join(set_clause),
        sql.SQL(" AND ").join(where_clause)
    )

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query.as_string(conn), values)
            conn.commit()
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    finally:
        db.release_connection(conn)


def delete_rows(table, filters):
    where_clause = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in filters]
    values = list(filters.values())

    query = sql.SQL("DELETE FROM {} WHERE {} RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(" AND ").join(where_clause)
    )

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query.as_string(conn), values)
            conn.commit()
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    finally:
        db.release_connection(conn)


def create_table(table, columns):
    column_defs = [f"{col} {dtype}" for col, dtype in columns.items()]
    query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.SQL(col) for col in column_defs)
    )

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            sql_str = query.as_string(conn)
            print(f"[DEBUG] Executing SQL: {sql_str}")
            cur.execute(sql_str)
            conn.commit()
    except Exception as e:
        print(f"[ERROR] Table creation failed: {e}")
        raise
    finally:
        db.release_connection(conn)