from typing import Dict, Any
from .tools import TOOLS
from .logger_config import logger

def extract_functions(state: Dict[str, Any], tools):
    code = state.get("code", "")
    funcs = []
    current = []
    for line in code.splitlines():
        if line.strip().startswith("def "):
            if current:
                funcs.append("\n".join(current))
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        funcs.append("\n".join(current))
    state["functions"] = funcs
    state.setdefault("quality_score", 0)
    logger.debug("extract_functions found %d functions", len(funcs))
    return {"n_functions": len(funcs)}

def check_complexity(state: Dict[str, Any], tools):
    funcs = state.get("functions", [])
    complexities = []
    for fn in funcs:
        r = tools["complexity"](fn)
        complexities.append(r["complexity"])
    state["complexities"] = complexities
    avg = sum(complexities)/len(complexities) if complexities else 0
    state["quality_score"] = max(0, 10 - avg)
    threshold = state.get("threshold", 7)
    state["_last_condition"] = "true" if state["quality_score"] < threshold else "false"
    logger.debug("check_complexity avg=%.2f quality_score=%.2f threshold=%s", avg, state["quality_score"], threshold)
    return {"avg_complexity": avg, "quality_score": state["quality_score"]}

def detect_issues(state: Dict[str, Any], tools):
    funcs = state.get("functions", [])
    issues = 0
    for fn in funcs:
        res = tools["detect_smells"](fn)
        issues += res.get("issues", 0)
    state["issues"] = issues
    logger.debug("detect_issues found %d issues", issues)
    return {"issues": issues}

def suggest_improvements(state: Dict[str, Any], tools):
    fixes = []
    for i, fn in enumerate(state.get("functions", [])):
        if len(fn.splitlines()) > 50:
            fixes.append({"func_index": i, "suggestion": "Split into smaller functions"})
    state["quality_score"] = min(10, state.get("quality_score", 0) + len(fixes)*2)
    threshold = state.get("threshold", 7)
    state["_last_condition"] = "true" if state["quality_score"] < threshold else "false"
    logger.debug("suggest_improvements applied %d fixes new_score=%.2f", len(fixes), state["quality_score"])
    return {"fixes": fixes, "quality_score": state["quality_score"]}

NODE_REGISTRY = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_issues": detect_issues,
    "suggest_improvements": suggest_improvements,
}

EXAMPLE_GRAPH = {
    "nodes": {
        "extract": {"name": "extract", "fn": "extract_functions"},
        "complexity": {"name": "complexity", "fn": "check_complexity"},
        "issues": {"name": "issues", "fn": "detect_issues"},
        "improve": {"name": "improve", "fn": "suggest_improvements"},
    },
    "edges": {
        "extract": "complexity",
        "complexity": {"true": "improve", "false": "issues", "default": "issues"},
        "improve": "complexity"
    }
}
