from enum import Enum
from pydantic import BaseModel

class PatchDeltaType(str, Enum):
    FUNCTION_DEF = "function"
    CLASS_DEF = "class"
    IMPORT = "import"

class ChangeClass(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"

class PatchDelta(BaseModel):
    node_type: str
    change_type: str
    detail: str

class PatchASTProposal(BaseModel):
    file_path: str
    base_sha: str
    updated_content: str
    risk_score: float
    risk_class: str
    diff_summary: str
    manual: bool
