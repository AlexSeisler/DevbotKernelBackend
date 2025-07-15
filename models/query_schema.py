from pydantic import BaseModel, Field
from typing import Optional, Literal
import json

class QueryRequest(BaseModel):
    table: Literal["file_structure_cache"]
    filters: Optional[str] = Field(
        default="{}",
        example='{"repo_id": "AlexSeisler/DevbotKernelBackend", "file_path": "sandbox/test.py", "branch": "main", "anchor_path": ["greet_user"]}'
    )
    limit: Optional[int] = 100
    order_by: Optional[str] = None
    desc: Optional[bool] = False

    def parsed_filters(self):
        return json.loads(self.filters or "{}")
