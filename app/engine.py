import asyncio
import time
from typing import Callable, Dict, Any, Optional
from .storage import GRAPHS, RUNS, LOG_QUEUES
from .models import RunState
from .logger_config import logger

MAX_STEPS = 500

async def _call_node(fn, state, tools):
    if asyncio.iscoroutinefunction(fn):
        return await fn(state, tools)
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(state, tools))

async def _emit_log(run_id: str, entry: dict):
    # append to stored run log
    run = RUNS.get(run_id)
    if run:
        run.log.append(entry)
    # push to websocket queue if exists (non-blocking)
    q = LOG_QUEUES.get(run_id)
    if q:
        try:
            await q.put(entry)
        except asyncio.CancelledError:
            logger.warning("log queue put cancelled for run %s", run_id)

async def run_graph(graph_id: str, initial_state: Dict, run_id: str, node_registry: Dict[str, Callable], tools: Dict[str, Callable]):
    graph = GRAPHS.get(graph_id)
    if not graph:
        raise ValueError("graph not found")

    run = RunState(run_id=run_id, graph_id=graph_id, state=initial_state, status="running", log=[])
    RUNS[run_id] = run

    # create queue for streaming logs
    LOG_QUEUES[run_id] = asyncio.Queue()

    nodes = list(graph.nodes.keys())
    if not nodes:
        run.status = "failed"
        await _emit_log(run_id, {"time": time.time(), "msg": "graph has no nodes"})
        return run

    current = nodes[0]
    steps = 0
    try:
        while current and steps < MAX_STEPS:
            steps += 1
            start_entry = {"time": time.time(), "node": current, "msg": "started"}
            logger.info("run %s - %s", run_id, start_entry)
            await _emit_log(run_id, start_entry)

            node_def = graph.nodes.get(current)
            if not node_def:
                err = {"time": time.time(), "node": current, "msg": "node definition not found"}
                await _emit_log(run_id, err)
                run.status = "failed"
                break

            fn_name = node_def.fn
            fn = node_registry.get(fn_name)
            if fn is None:
                err = {"time": time.time(), "node": current, "msg": f"fn {fn_name} not found"}
                await _emit_log(run_id, err)
                run.status = "failed"
                break

            try:
                result = await _call_node(fn, run.state, tools)
                finished_entry = {"time": time.time(), "node": current, "msg": "finished", "result": result}
                await _emit_log(run_id, finished_entry)
                logger.info("run %s - %s", run_id, finished_entry)
            except Exception as e:
                err = {"time": time.time(), "node": current, "msg": "error", "error": str(e)}
                await _emit_log(run_id, err)
                logger.exception("error in node %s for run %s: %s", current, run_id, e)
                run.status = "failed"
                break

            raw_next = graph.edges.get(current)
            next_node = None
            if isinstance(raw_next, str):
                next_node = raw_next
            elif isinstance(raw_next, dict):
                key = run.state.get("_last_condition")
                if key and key in raw_next:
                    next_node = raw_next[key]
                else:
                    next_node = raw_next.get("default")
            else:
                next_node = None

            if not next_node:
                current = None
                break
            else:
                current = next_node

        else:
            if steps >= MAX_STEPS:
                await _emit_log(run_id, {"time": time.time(), "msg": "max steps exceeded; aborting"})
                run.status = "failed"
                return run

        run.status = "finished"
        await _emit_log(run_id, {"time": time.time(), "msg": "run_finished", "status": run.status})
        return run

    except Exception as e:
        run.status = "failed"
        await _emit_log(run_id, {"time": time.time(), "msg": "engine_error", "error": str(e)})
        logger.exception("engine error for run %s: %s", run_id, e)
        return run
    finally:
        # close queue to signal consumers - put a sentinel then delete
        q = LOG_QUEUES.get(run_id)
        if q:
            # put sentinel
            try:
                await q.put({"time": time.time(), "msg": "stream_end"})
            except Exception:
                pass
            # keep queue available briefly for readers to drain; we don't delete immediately
