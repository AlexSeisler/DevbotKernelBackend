#Placeholder for db_write.py
from fastapi import APIRouter, HTTPException
from models.query_schema import InsertRequest, UpdateRequest, DeleteRequest, CreateTableRequest
from services.db.query_executor import insert_rows, update_rows, delete_rows, create_table
from settings import Database

router = APIRouter()
db = Database()
@router.post("/insert")
async def insert_handler(req: InsertRequest):
    try:
        return insert_rows(req.table, req.rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update")
async def update_handler(req: UpdateRequest):
    try:
        return update_rows(req.table, req.filters, req.updates)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete")
async def delete_handler(req: DeleteRequest):
    try:
        return delete_rows(req.table, req.filters)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-table")
async def create_table_handler(req: CreateTableRequest):
    try:
        create_table(req.table, req.columns)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/introspect/tables")
async def introspect_tables():
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')")
            rows = cur.fetchall()
            return [row[0] for row in rows]
    finally:
        db.release_connection(conn)