from __future__ import annotations
from typing import Dict, List, Literal
from arrow_pratt import risk_index_from_choices
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


GAME_SCENARIOS_PROPERTIES: List[Dict[str, any]] = [
    {"id": 1, "safe_value": 10.0, "risky_options": [{"prob": 0.5, "value": 30.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 2, "safe_value": 15.0, "risky_options": [{"prob": 0.5, "value": 30.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 3, "safe_value": 20.0, "risky_options": [{"prob": 0.5, "value": 40.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 4, "safe_value": 25.0, "risky_options": [{"prob": 0.5, "value": 40.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 5, "safe_value": 30.0, "risky_options": [{"prob": 0.5, "value": 50.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 6, "safe_value": 35.0, "risky_options": [{"prob": 0.5, "value": 50.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 7, "safe_value": 40.0, "risky_options": [{"prob": 0.5, "value": 60.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 8, "safe_value": 45.0, "risky_options": [{"prob": 0.5, "value": 60.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 9, "safe_value": 50.0, "risky_options": [{"prob": 0.5, "value": 70.0}, {"prob": 0.5, "value": 0.0}]},
    {"id": 10, "safe_value": 55.0, "risky_options": [{"prob": 0.5, "value": 70.0}, {"prob": 0.5, "value": 0.0}]},
]

def calculate_expected_value(options: List[Dict[str, float]]) -> float:
    expected_value = 0.0
    for option in options:
        expected_value += option["prob"] * option["value"]
    return expected_value

def calculate_risk_game_score_with_prat(
        choices: List[Literal["safe", "risky"]],
        scenario_properties: List[Dict[str, any]]
) -> float:
    return risk_index_from_choices(choices, scenario_properties)



def calculate_risk_game_score_with_aversion_formula(
        choices: List[Literal["safe", "risky"]],
        scenario_properties: List[Dict[str, any]]
) -> float:
    """
    Calculates a risk score (0=more cautious/averse, 1=more bold/seeking) based on choices relative to expected values.
    """
    if not choices or len(choices) != len(scenario_properties):
        raise ValueError("Mismatch between choices and scenario definitions")
        # todo :: compare this returns and exception::  return 0.5 neutral score

    round_scores: List[float] = []

    for index, choice_made in enumerate(choices):
        scenario = scenario_properties[index]
        safe_expected_value = scenario["safe_value"]
        risky_expected_value = calculate_expected_value(scenario["risky_options"])

        certainty_equivalent = risky_expected_value - safe_expected_value
        round_score = 0.5

        if choice_made == "risky":
            if certainty_equivalent >= 0:
                # Chose risky, and it was rational (EV_risky >= EV_safe)
                # Score increases slightly above neutral, more if premium is large
                round_score = 0.6 + 0.4 * min(1, max(0, certainty_equivalent / (safe_expected_value + 1e-9)))
            else:
                # Chose risky even though EV_risky < EV_safe (clear risk-seeking)
                round_score = 1.0
        elif choice_made == "safe":
            if certainty_equivalent >= 0:
                # Chose safe even though EV_risky > EV_safe (clear risk-aversion)
                # They gave up `certainty_equivalent_premium_for_risky` in EV.
                # Score decreases from neutral, more if premium foregone is large.
                round_score = 0.4 - 0.4 * min(1, max(0, certainty_equivalent / (risky_expected_value + 1e-9)))
            else:
                # Chose safe, and it was rational (EV_safe >= EV_risky)
                round_score = 0.2

        round_scores.append(max(0.0, min(1.0, round_score)))

    if not round_scores:
        return 0.5

    final_score = sum(round_scores) / len(round_scores)
    return final_score

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
        # return calculate_risk_game_score_with_prat(
        #     request_payload["choices"],
        #     GAME_SCENARIOS_PROPERTIES
        # )
        return calculate_risk_game_score_with_aversion_formula(
            request_payload["choices"],
            GAME_SCENARIOS_PROPERTIES
        )

    raise ValueError(f"Unknown game type: {game_type}")