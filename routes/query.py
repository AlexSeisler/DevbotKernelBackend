from fastapi import APIRouter, HTTPException, Body
from models.query_schema import QueryRequest
from services.db.query_executor import execute_query, db

router = APIRouter()

@router.post("/query")
async def query_table(request: QueryRequest = Body(...)):
    try:
        print("✅ /query reached: Request payload =", request.dict())

        filters_dict = request.parsed_filters()

        rows = execute_query(
            db=db,
            table=request.table,
            filters=filters_dict,
            limit=request.limit,
            order_by=request.order_by,
            desc=request.desc
        )

        return {"rows": rows}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Bad Request: {str(ve)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
