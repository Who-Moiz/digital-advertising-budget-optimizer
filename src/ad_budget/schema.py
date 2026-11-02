"""Shared data contract and strict validation."""

import numpy as np
import pandas as pd

PLATFORMS = ("Facebook", "Instagram", "Google", "TikTok", "YouTube")
DIMENSIONS = ("platform", "campaign", "date", "age", "gender", "city", "device")
MEASURES = ("impressions", "clicks", "spend", "conversions", "revenue")
COLUMNS = ("date", "campaign", "platform", *MEASURES, "age", "gender", "city", "device")
COUNTS = ("impressions", "clicks", "conversions")


def validate(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate without silently coercing or dropping bad records."""
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError("Dataset must contain at least one row.")
    if frame[list(COLUMNS)].isna().any().any():
        raise ValueError("Required columns contain null values.")
    for col in (*MEASURES, "age"):
        if not pd.api.types.is_numeric_dtype(frame[col]):
            raise ValueError(f"{col} must be numeric.")
        if not np.isfinite(frame[col].to_numpy(dtype=float)).all() or (frame[col] < 0).any():
            raise ValueError(f"{col} must contain finite, non-negative values.")
    for col in (*COUNTS, "age"):
        if (frame[col] % 1 != 0).any():
            raise ValueError(f"{col} must contain whole numbers.")
    if (frame.clicks > frame.impressions).any() or (frame.conversions > frame.clicks).any():
        raise ValueError("Counts must satisfy conversions <= clicks <= impressions.")
    if not frame.platform.isin(PLATFORMS).all():
        raise ValueError(f"Platform must be one of {PLATFORMS}.")
    if not frame.age.between(18, 100).all():
        raise ValueError("Age must be between 18 and 100.")
    for col in DIMENSIONS:
        if frame[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"{col} cannot contain blank values.")
    if pd.to_datetime(frame.date, format="%Y-%m-%d", errors="coerce").isna().any():
        raise ValueError("Dates must use YYYY-MM-DD.")
    return frame
