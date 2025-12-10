from typing import Callable, Dict

def detect_smells(code: str):
    issues = 0
    if "goto" in code:
        issues += 1
    if len(code.splitlines()) > 200:
        issues += 1
    return {"issues": issues}

def complexity_of_function(fn_code: str):
    score = sum(fn_code.count(k) for k in ("if ", "for ", "while "))
    return {"complexity": score}

TOOLS: Dict[str, Callable] = {
    "detect_smells": detect_smells,
    "complexity": complexity_of_function,
}
