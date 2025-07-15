from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal

class QueryRequest(BaseModel):
    table: Literal["file_structure_cache"]
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        example={
            "repo_id": "AlexSeisler/DevbotKernelBackend",
            "file_path": "sandbox/test.py",
            "branch": "main",
            "anchor_path": ["greet_user"]
        }
    )
    limit: Optional[int] = 100
    order_by: Optional[str] = None
    desc: Optional[bool] = False
