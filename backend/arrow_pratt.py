from __future__ import annotations
from typing import List, Dict, Literal, Tuple
import math
import numpy as np
from scipy.optimize import minimize
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _crra_utility(x: float, rho: float) -> float:
    """
    Constant-Relative-Risk-Aversion utility.
      u(x) = x^(1-rho)/(1-rho)      if rho ≠ 1
      u(x) = log(x)                 if rho = 1        (limit case)
    """
    if rho == 1.0:
        return math.log(max(x, 1e-9))
    return (max(x, 1e-9) ** (1.0 - rho)) / (1.0 - rho)

def _expected_utility(lottery, rho: float) -> float:
    """
    Accepts a list of either
      • (payoff, prob) tuples      OR
      • {'value': payoff, 'prob': p} dicts
    """
    eu = 0.0
    for item in lottery:
        if isinstance(item, dict):
            payoff = float(item["value"])
            prob   = float(item.get("prob", 1.0 / len(lottery)))
        else:
            payoff, prob = item
        eu += _crra_utility(payoff, rho) * prob
    return eu

def _safe_sigmoid(x: float) -> float:
    """
    Numerically stable σ(x).   Uses tanh for |x|>20 so we never call exp()
    outside the safe range.
    """
    if x > 20:           # exp(-x) would underflow
        return 1.0
    if x < -20:          # exp(-x) would overflow
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _choice_loglik(
        rho: float,
        choices: List[Literal["safe", "risky"]],
        scenarios: List[Dict],
        temperature: float,  # Temperature is now a required parameter
) -> float:
    ll = 0.0
    epsilon = 1e-9

    # Ensure temperature is positive and reasonably sized
    if temperature <= 1e-6:
        # logger.warning(f"Temperature ({temperature}) is too small or non-positive. Clamping to 1e-6.")
        current_temp = 1e-6
    else:
        current_temp = temperature

    for ch, sc in zip(choices, scenarios):
        eu_safe = _crra_utility(sc["safe_value"], rho)
        eu_risky = _expected_utility(sc["risky_options"], rho)

        delta = (eu_risky - eu_safe) / current_temp
        p_risky = _safe_sigmoid(delta)

        if ch == "risky":
            prob_chosen = p_risky
        else:  # ch == "safe"
            prob_chosen = 1.0 - p_risky

        ll += math.log(max(prob_chosen, epsilon))

    return -ll


def arrow_pratt_from_choices(
        choices: List[Literal["safe", "risky"]],
        scenarios: List[Dict],
        wealth_base: float | None = None,
        rho_bounds: Tuple[float, float] = (-4.0, 4.0),  # MODIFIED: Wider default bounds
        initial_rho: float = 0.0,  # MODIFIED: Default initial rho to 0 (neutral)
        temperature: float = 1.0  # ADDED: Temperature parameter
) -> Tuple[float, float]:
    """
    Returns (rho_hat, A(w))  — the estimated CRRA curvature and
    the Arrow–Pratt coefficient evaluated at wealth w.
    rho_hat > 0: risk-averse
    rho_hat = 0: risk-neutral
    rho_hat < 0: risk-seeking
    """
    if not choices or len(choices) != len(scenarios):
        # Log error or return a default if appropriate for your application upon failure
        raise ValueError("Choices and scenarios length mismatch or choices list is empty.")

    logger.info(f"Estimating rho with {len(choices)} choices, temperature: {temperature}, initial_rho: {initial_rho}, bounds: {rho_bounds}")

    res = minimize(
        lambda r_arr: _choice_loglik(r_arr[0], choices, scenarios, temperature=temperature),
        x0=[initial_rho],
        bounds=[rho_bounds],  # Pass as a list containing one tuple for the single variable
        method="L-BFGS-B",
    )

    if not res.success:
        logger.warning(
            f"Optimization for rho_hat did not succeed: {res.message}. Using result x: {res.x[0]:.4f} (status: {res.status})")

    rho_hat = float(res.x[0])
    # Clip rho_hat to bounds just in case optimizer slightly oversteps due to numerical precision
    rho_hat = max(rho_bounds[0], min(rho_hat, rho_bounds[1]))

    # Calculate wealth_base for A_w
    if wealth_base is None:
        if scenarios:  # Check if scenarios list is not empty
            # Filter for valid, finite safe_values before calculating mean
            safe_values = [
                float(sc["safe_value"]) for sc in scenarios
                if "safe_value" in sc and np.isfinite(float(sc["safe_value"]))
            ]
            if safe_values:
                wealth_base = np.mean(safe_values)
            else:
                # logger.warning("No valid (finite) safe_values found in scenarios to compute wealth_base. Defaulting to 1.0.")
                wealth_base = 1.0
        else:
            # logger.warning("Scenarios list is empty, cannot compute wealth_base. Defaulting to 1.0.")
            wealth_base = 1.0

    A_w = rho_hat / max(wealth_base, 1e-6)  # Ensure wealth_base is positive
    return rho_hat, A_w

def risk_index_from_choices(
    choices: List[Literal["safe", "risky"]],
    scenarios: List[Dict],
    wealth_base: float | None = None,
    rho_bounds_for_estimation: Tuple[float, float] = (-4.0, 4.0), # Allow configuring estimation bounds
    initial_rho_for_estimation: float = 0.0,
    temperature_for_estimation: float = 1.0 # Allow configuring temperature
) -> float:
    """
    Converts the CRRA estimate (rho_hat) into a bounded 0–1 index.
    The rho_hat is estimated, typically within bounds like [-4.0, 4.0].
    The index is calculated as 1.0 / (1.0 + exp(rho_hat)).
    This maps:
        rho_hat = -4.0 (strong risk-seeking) -> index ≈ 0.982 (close to 1)
        rho_hat =  0.0 (risk-neutral)       -> index = 0.5
        rho_hat =  4.0 (strong risk-averse)  -> index ≈ 0.018 (close to 0)
    """
    if not choices:
        logger.warning("risk_index_from_choices called with empty choices list. Returning neutral index 0.5.")
        return 0.5 # Return a neutral/default score

    try:
        rho_hat, _ = arrow_pratt_from_choices(
            choices,
            scenarios,
            wealth_base,
            rho_bounds=rho_bounds_for_estimation,
            initial_rho=initial_rho_for_estimation,
            temperature=temperature_for_estimation # Pass temperature
        )
    except ValueError as e:
        logger.error(f"ValueError during rho estimation (e.g., input mismatch): {e}. Returning neutral index 0.5.")
        return 0.5
    except Exception as e: # Catch any other unexpected errors during optimization
        logger.error(f"Unexpected error during rho estimation: {e}. Returning neutral index 0.5.")
        return 0.5

    logger.info(f"Estimated rho_hat for index calculation: {rho_hat:.4f}")

    # Transformation: sigmoid(-rho_hat) which is 1 / (1 + exp(rho_hat))
    risk_index = 1.0 / (1.0 + math.exp(rho_hat))

    logger.info(f"Calculated risk_index: {risk_index:.4f}")
    return risk_index