from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ToolParameter(BaseModel):
    name: str
    type: str

class Tool(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]

class ModelContextRequest(BaseModel):
    verb: str
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None

class ModelContextResponse(BaseModel):
    tools: Optional[List[Tool]] = None
    result: Optional[Any] = None

