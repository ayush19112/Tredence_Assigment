from typing import Dict
from .models import GraphDef, RunState
import asyncio

GRAPHS: Dict[str, GraphDef] = {}
RUNS: Dict[str, RunState] = {}

# per-run asyncio.Queue for streaming logs to WebSocket clients
LOG_QUEUES: Dict[str, asyncio.Queue] = {}
