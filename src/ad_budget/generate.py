"""Bounded-memory, seeded synthetic advertising data generation."""

from pathlib import Path

import numpy as np
import pandas as pd

from ad_budget.schema import COLUMNS, PLATFORMS


def generate_csv(
    path: str | Path, rows: int = 10_000, seed: int = 42, chunk_size: int = 100_000
) -> Path:
    """Write realistic funnel counts and PKR currency, never holding all rows."""
    if rows <= 0 or chunk_size <= 0:
        raise ValueError("rows and chunk_size must be positive.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    # Synthetic assumptions, not observed platform performance.
    ctr = np.array([0.020, 0.026, 0.038, 0.031, 0.016])
    cvr = np.array([0.035, 0.040, 0.065, 0.025, 0.030])
    cpc = np.array([24.0, 27.0, 39.0, 15.0, 21.0])
    for start in range(0, rows, chunk_size):
        size = min(chunk_size, rows - start)
        platform = rng.integers(0, len(PLATFORMS), size)
        device = rng.choice(["Mobile", "Desktop", "Tablet"], size, p=[0.72, 0.23, 0.05])
        impressions = rng.integers(400, 12_001, size)
        clicks = rng.binomial(impressions, ctr[platform])
        conversions = rng.binomial(
            clicks, np.minimum(cvr[platform] * np.where(device == "Desktop", 1.15, 1.0), 1)
        )
        spend = np.round(clicks * cpc[platform] * rng.uniform(0.75, 1.25, size), 2)
        revenue = np.round(conversions * rng.lognormal(np.log(1600), 0.22, size), 2)
        dates = np.datetime64("2025-01-01") + rng.integers(0, 365, size).astype("timedelta64[D]")
        names = np.array(PLATFORMS)[platform]
        frame = pd.DataFrame(
            {
                "date": dates.astype(str),
                "campaign": [
                    f"{p.lower()}_campaign_{n:02}" for p, n in zip(names, rng.integers(1, 9, size))
                ],
                "platform": names,
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "conversions": conversions,
                "revenue": revenue,
                "age": rng.integers(18, 66, size),
                "gender": rng.choice(["Female", "Male", "Unspecified"], size, p=[0.47, 0.47, 0.06]),
                "city": rng.choice(
                    ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad"], size
                ),
                "device": device,
            },
            columns=COLUMNS,
        )
        frame.to_csv(path, index=False, mode="w" if start == 0 else "a", header=start == 0)
    return path
