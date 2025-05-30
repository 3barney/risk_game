from __future__ import annotations
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def single_shot(choice: str) -> float:
    return 1.0 if choice == "risky" else 0.0

def multi_shot_logic(choices: List[str]) -> float:
    try:
        # This calculates risk based on when the user first switched to "safe"
        # If they never choose "safe", switch_index becomes len(choices)
        switch_index = choices.index("safe")
    except ValueError:
        switch_index = len(choices)

    if not choices:
        return 0.0
    return switch_index / len(choices)

def slider_question(certainty: float, prize: float = 100.0) -> float:
    return max(0.0, min(1.0, (prize - certainty) / prize))

def balloon_question(pumps: int, popped: bool, max_safe: int = 20) -> float:
    effective = pumps + (1 if popped else 0)
    return min(effective, max_safe) / max_safe

def budget_split(risky_tokens: int,
                 total: int = 100) -> float:
    return risky_tokens / total

def compute_risk(request_payload: Dict) -> float:
    game_type = request_payload["game"]
    logger.info(f"Game type: {game_type}")

    if game_type == "single":
        return single_shot(request_payload["choice"])
    if game_type == "multiple":
        return multi_shot_logic(request_payload["choices"])
    if game_type == "slider":
        return slider_question(request_payload["certainty"])
    if game_type == "balloon":
        return balloon_question(request_payload["pumps"], request_payload["popped"])
    if game_type == "budget":
        return budget_split(request_payload["risky_tokens"])
    if game_type == "risk":
        return multi_shot_logic(request_payload["choices"])

    raise ValueError(f"Unknown game type: {game_type}")