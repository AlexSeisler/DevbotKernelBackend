from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
import json

class QueryRequest(BaseModel):
    table: str  # removed enum constraint
    filters: str  # JSON stringified filter object
    limit: Optional[int] = 100
    order_by: Optional[str]
    desc: Optional[bool] = False

    def parsed_filters(self) -> Dict[str, Any]:
        return json.loads(self.filters)
from typing import List, Dict, Any

class InsertRequest(BaseModel):
    table: str
    rows: str  # stringified JSON array of dicts

class UpdateRequest(BaseModel):
    table: str
    filters: str  # stringified JSON
    updates: str  # stringified JSON

    def parsed_filters(self) -> Dict[str, Any]:
        return json.loads(self.filters)

    def parsed_updates(self) -> Dict[str, Any]:
        return json.loads(self.updates)
    table: str
    filters: Dict[str, Any]
    updates: Dict[str, Any]

class DeleteRequest(BaseModel):
    table: str
    filters: Dict[str, Any]

class CreateTableRequest(BaseModel):
    table: str
    columns: Dict[str, str]  # column_name: SQL type string