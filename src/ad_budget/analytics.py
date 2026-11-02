"""Consistent weighted KPIs derived from additive funnel totals."""

from pathlib import Path

import numpy as np
import pandas as pd

from ad_budget.schema import DIMENSIONS, MEASURES, validate


def with_kpis(totals: pd.DataFrame) -> pd.DataFrame:
    result = totals.copy()
    for name, numerator, denominator, scale in (
        ("ctr", "clicks", "impressions", 100),
        ("cpc", "spend", "clicks", 1),
        ("cpa", "spend", "conversions", 1),
        ("conversion_rate", "conversions", "clicks", 100),
        ("roas", "revenue", "spend", 1),
    ):
        result[name] = result[numerator].div(result[denominator].replace(0, np.nan)) * scale
    result["profit_proxy"] = result.revenue - result.spend
    return result


def aggregate(frame: pd.DataFrame, group_by: str = "platform") -> pd.DataFrame:
    if group_by not in DIMENSIONS:
        raise ValueError(f"group_by must be one of {DIMENSIONS}.")
    totals = frame.groupby(group_by, observed=True, sort=True)[list(MEASURES)].sum().reset_index()
    return with_kpis(totals)


def pandas_analyze(path: str | Path, group_by: str = "platform") -> pd.DataFrame:
    frame = validate(pd.read_csv(path))
    return aggregate(frame, group_by)


def chunked_analyze(
    path: str | Path, group_by: str = "platform", chunk_size: int = 100_000
) -> pd.DataFrame:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    partials = []
    for frame in pd.read_csv(path, chunksize=chunk_size):
        partial = aggregate(validate(frame), group_by)[[group_by, *MEASURES]]
        partials.append(partial)
        # Fold frequently so memory is bounded by chunk size and group cardinality.
        if len(partials) >= 8:
            partials = [pd.concat(partials).groupby(group_by)[list(MEASURES)].sum().reset_index()]
    if not partials:
        raise ValueError("Dataset must contain at least one row.")
    totals = pd.concat(partials).groupby(group_by)[list(MEASURES)].sum().reset_index()
    return with_kpis(totals)
