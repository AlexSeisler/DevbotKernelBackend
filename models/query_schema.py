from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

class QueryRequest(BaseModel):
    table: str  # removed enum constraint
    filters: str  # JSON stringified filter object
    limit: Optional[int] = 100
    order_by: Optional[str]
    desc: Optional[bool] = False

    def parsed_filters(self) -> Dict[str, Any]:
        return json.loads(self.filters)


class InsertRequest(BaseModel):
    table: str
    rows: str  # stringified JSON array of dicts

    def parsed_rows(self) -> List[Dict[str, Any]]:
        return json.loads(self.rows)


class UpdateRequest(BaseModel):
    table: str
    filters: str  # stringified JSON
    updates: str  # stringified JSON

    def parsed_filters(self) -> Dict[str, Any]:
        return json.loads(self.filters)

    def parsed_updates(self) -> Dict[str, Any]:
        return json.loads(self.updates)


class DeleteRequest(BaseModel):
    table: str
    filters: str  # stringified JSON

    def parsed_filters(self) -> Dict[str, Any]:
        return json.loads(self.filters)


class CreateTableRequest(BaseModel):
    table: str
    columns: str  # stringified JSON

    def parsed_columns(self) -> Dict[str, str]:
        return json.loads(self.columns)
class ProjectTaskQueue(BaseModel):
    id: Optional[str]
    project_name: str
    repo_id: str
    phase: Optional[str]
    subsystem: Optional[List[str]]
    file_path: Optional[str]
    context_files: Optional[List[str]] = []
    description: str
    priority: Optional[int] = 2
    status: Optional[str] = "idea"  # matches task_status enum
    dependencies: Optional[List[str]] = []
    security_flags: Optional[Dict[str, Any]] = {}
    created_by: Optional[str]
    executed_by: Optional[str]
    execution_summary: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]