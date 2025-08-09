from services.db.query_executor import execute_query, insert_rows
from typing import Dict, Any, List

TABLE_NAME = "project_task_queue"

def insert_project_task(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Insert a new project_task_queue record.
    """
    return insert_rows(TABLE_NAME, [row])

def get_project_tasks(
    filters: Dict[str, Any] = None,
    limit: int = 100,
    order_by: str = "created_at",
    desc: bool = True
) -> List[Dict[str, Any]]:
    """
    Query project_task_queue with optional filters.
    """
    return execute_query(
        db=None,  # query_executor handles global _db_instance
        table=TABLE_NAME,
        filters=filters,
        limit=limit,
        order_by=order_by,
        desc=desc
    )
