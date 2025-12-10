from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class NodeDef(BaseModel):
    name: str
    fn: str

class GraphDef(BaseModel):
    nodes: Dict[str, NodeDef]
    edges: Dict[str, Any]

class RunRequest(BaseModel):
    graph_id: str
    initial_state: dict = {}
    background: bool = False  # if true, start run in background and return run_id immediately

class RunState(BaseModel):
    run_id: str
    graph_id: str
    status: str = "running"  # running | finished | failed
    state: Dict[str, Any] = Field(default_factory=dict)
    log: list = Field(default_factory=list)
