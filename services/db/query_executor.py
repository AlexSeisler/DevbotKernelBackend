from psycopg2 import sql
from settings import _db_instance

db = _db_instance


def execute_query(db: Database, table: str, filters: dict = None, limit: int = 100, order_by: str = None, desc: bool = False, columns: list = None):
    filters = filters or {}

    # Determine which columns to select
    if columns:
        base = sql.SQL("SELECT {} FROM {} ").format(
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.Identifier(table)
        )
    else:
        base = sql.SQL("SELECT * FROM {} ").format(sql.Identifier(table))

    # Build WHERE clause from filters
    conditions = []
    values = []
    for k, v in filters.items():
        if isinstance(v, list):
            conditions.append(sql.SQL("{} = ANY(%s)").format(sql.Identifier(k)))
            values.append(v)
        else:
            conditions.append(sql.SQL("{} = %s").format(sql.Identifier(k)))
            values.append(v)

    if conditions:
        base += sql.SQL("WHERE ") + sql.SQL(" AND ").join(conditions)

    # Ordering
    if order_by:
        base += sql.SQL(" ORDER BY {} {}").format(
            sql.Identifier(order_by),
            sql.SQL("DESC" if desc else "ASC")
        )

    # Limit
    base += sql.SQL(" LIMIT %s")
    values.append(limit)

    rows = db.fetch_all(base, values)
    return [dict(row) for row in rows]
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