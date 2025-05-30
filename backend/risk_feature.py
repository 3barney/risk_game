from __future__ import annotations
from typing import Dict, List

# sinle question
def single_shot(choice: str) -> float:
    return 1.0 if choice == "risky" else 0.0

# Multiple question
def multi_shot(choices: List[str]) -> float:
    try:
        switch_index = choices.index("safe")
    except ValueError:
        switch_index = len(choices)
    return switch_index / len(choices)

# slider quiz
def slider_question(certainty: float, prize: float = 100.0) -> float:
    return 1.0 - certainty / prize

def ballon_question(pumps: int, popped: bool, max_safe: int = 20) -> float:
    # on poppped, add user +1 as willing to wait
    effective = pumps + (1 if popped else 0)
    return min(effective, max_safe) / max_safe

def budget_split(risk_tokens: int, total: int = 10) -> float:
    return risk_tokens / total

def compute_risk(request_payload: Dict) -> float:
    question = request_payload["game"]
    if question == "single":
        return single_shot(request_payload["choice"])
    if question == "multiple":
        return multi_shot(request_payload["choice"])
    if question == "slider":
        return slider_question(request_payload["certainty"])
    if question == "ballon":
        return ballon_question(request_payload["pumps"], request_payload["popped"])
    if question == "budget":
        return budget_split(request_payload["risk_tokens"])
    raise ValueError(f"Unknown game question: {question}")
