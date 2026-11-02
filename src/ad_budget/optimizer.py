"""Constrained allocation under an explicit diminishing-returns scenario model."""

from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd


def recommend(
    performance: pd.DataFrame,
    budget: float = 1_000_000,
    min_share: float = 0.05,
    max_share: float = 0.45,
    prior_strength: float = 50_000,
    saturation: float = 0.75,
    steps: int = 10_000,
) -> pd.DataFrame:
    """Allocate integer paisa by greedy marginal returns on a concave response.

    Historical ROAS is shrunk toward pooled ROAS. A log response encodes diminishing
    returns; it is a transparent assumption, not an estimated causal response curve.
    """
    if not np.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive.")
    if not (0 <= min_share <= max_share <= 1):
        raise ValueError("Shares must satisfy 0 <= min_share <= max_share <= 1.")
    if not np.isfinite(prior_strength) or prior_strength <= 0:
        raise ValueError("prior_strength must be finite and positive.")
    if not np.isfinite(saturation) or saturation <= 0 or steps < 1:
        raise ValueError("saturation and steps must be positive.")
    required = {"platform", "spend", "revenue", "conversions"}
    if not required.issubset(performance):
        raise ValueError(f"Performance requires {sorted(required)}.")
    data = performance.sort_values("platform").reset_index(drop=True).copy()
    if data.empty or data.platform.duplicated().any() or data.platform.isna().any():
        raise ValueError("Supply one non-empty row per platform.")
    numeric = data[["spend", "revenue", "conversions"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (numeric < 0).any() or data.spend.sum() <= 0:
        raise ValueError("Historical totals must be finite, non-negative, with positive spend.")
    count = len(data)
    if count * min_share > 1 + 1e-12 or count * max_share < 1 - 1e-12:
        raise ValueError("Share bounds are infeasible for the number of platforms.")
    cents = int((Decimal(str(budget)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    lower = int(np.ceil(min_share * cents - 1e-9))
    upper = int(np.floor(max_share * cents + 1e-9))
    if cents < 1 or count * lower > cents or count * upper < cents:
        raise ValueError("Budget is too small to satisfy share bounds at paisa precision.")
    pooled = data.revenue.sum() / data.spend.sum()
    score = ((data.revenue + prior_strength * pooled) / (data.spend + prior_strength)).to_numpy()
    historical_share = (data.spend / data.spend.sum()).to_numpy()
    scale = np.maximum(historical_share * (cents / 100), (cents / 100) / count * 0.25)
    allocation = np.full(count, lower, dtype=np.int64)
    remaining = cents - int(allocation.sum())
    quantum = max(1, cents // steps)
    while remaining:
        capacity = upper - allocation
        delta = np.minimum(capacity, min(quantum, remaining))
        current = allocation / 100
        # Average gain per unit accounts for unequal remaining capacity.
        gain = (
            score
            * scale
            / saturation
            * np.log1p(saturation * (delta / 100) / (scale + saturation * current))
        )
        marginal = np.divide(gain, delta, out=np.full(count, -np.inf), where=delta > 0)
        winner = int(np.argmax(marginal))
        if delta[winner] <= 0:
            raise ValueError("No feasible allocation remains.")
        allocation[winner] += delta[winner]
        remaining -= int(delta[winner])
    amount = allocation / 100
    baseline = historical_share * (cents / 100)

    def response(x):
        return score * scale / saturation * np.log1p(saturation * x / scale)

    data["historical_share_pct"] = historical_share * 100
    data["adjusted_roas"] = score
    data["recommended_budget"] = amount
    data["recommended_share_pct"] = allocation / cents * 100
    data["share_change_pp"] = data.recommended_share_pct - data.historical_share_pct
    data["modeled_revenue"] = response(amount)
    data["baseline_modeled_revenue"] = response(baseline)
    data["evidence_weight"] = data.spend / (data.spend + prior_strength)
    return data
