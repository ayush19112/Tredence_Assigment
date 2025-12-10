from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from uuid import uuid4
from .models import GraphDef, RunRequest, RunState
from .storage import GRAPHS, RUNS, LOG_QUEUES
from .workflows import EXAMPLE_GRAPH, NODE_REGISTRY
from .tools import TOOLS
from .engine import run_graph
from .logger_config import logger
import asyncio

app = FastAPI(title="Workflow Engine (with Background, Logging, WebSocket)")

# bootstrap example graph at startup
@app.on_event("startup")
async def startup_event():
    gid = "example"
    try:
        GRAPHS[gid] = GraphDef.parse_obj(EXAMPLE_GRAPH)
        logger.info("Loaded example graph with id '%s'", gid)
    except Exception as e:
        logger.exception("Failed to load example graph: %s", e)

@app.post("/graph/create")
async def create_graph(payload: dict):
    graph_id = str(uuid4())
    if "nodes" not in payload or "edges" not in payload:
        raise HTTPException(400, "payload must include nodes and edges")
    GRAPHS[graph_id] = GraphDef.parse_obj(payload)
    logger.info("Created graph %s", graph_id)
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph_endpoint(req: RunRequest, background_tasks: BackgroundTasks):
    graph_id = req.graph_id
    if graph_id not in GRAPHS:
        raise HTTPException(404, "graph not found")
    run_id = str(uuid4())
    # create initial run state we'll store immediately
    RUNS[run_id] = RunState(run_id=run_id, graph_id=graph_id, status="running", state=req.initial_state, log=[])
    logger.info("Starting run %s for graph %s background=%s", run_id, graph_id, req.background)

    # start as background task (uvicorn will run it)
    async def _runner():
        try:
            await run_graph(graph_id, req.initial_state, run_id, NODE_REGISTRY, TOOLS)
        except Exception as e:
            logger.exception("Background runner failed for %s: %s", run_id, e)

    if req.background:
        # schedule background coroutine
        task = asyncio.create_task(_runner())
        # no need to keep handle; runs in event loop
        return {"run_id": run_id, "status": "started", "background": True}
    else:
        # run to completion and return final response
        run = await run_graph(graph_id, req.initial_state, run_id, NODE_REGISTRY, TOOLS)
        return {"run_id": run_id, "status": run.status, "final_state": run.state, "log": run.log}

@app.get("/graph/state/{run_id}")
async def get_run_state(run_id: str):
    r = RUNS.get(run_id)
    if not r:
        raise HTTPException(404, "run not found")
    return r

# WebSocket endpoint to stream logs for a run_id
@app.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()
    logger.info("WebSocket client connected for run %s", run_id)
    q = LOG_QUEUES.get(run_id)
    if q is None:
        # if queue not created yet, make one so runner can push when it starts
        q = asyncio.Queue()
        LOG_QUEUES[run_id] = q

    try:
        # send any existing logs first (if run exists)
        run = RUNS.get(run_id)
        if run:
            for entry in run.log:
                await websocket.send_json({"historic": True, "entry": entry})

        # Now stream new logs from queue
        while True:
            entry = await q.get()
            if entry is None:
                # sentinel (not used, kept for robustness)
                break
            # if stream_end, send then break
            await websocket.send_json({"live": True, "entry": entry})
            if entry.get("msg") == "stream_end":
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for run %s", run_id)
    except Exception as e:
        logger.exception("WebSocket error for run %s: %s", run_id, e)
    finally:
        logger.info("WebSocket handler finished for run %s", run_id)
