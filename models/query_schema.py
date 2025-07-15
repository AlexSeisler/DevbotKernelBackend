from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal

class QueryRequest(BaseModel):
    table: Literal["file_structure_cache"]
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 100
    order_by: Optional[str] = None
    desc: Optional[bool] = False
