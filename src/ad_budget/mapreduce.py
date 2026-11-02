"""Local process-based MapReduce with bounded pending chunks (not Hadoop)."""

from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import pandas as pd

from ad_budget.analytics import with_kpis
from ad_budget.schema import DIMENSIONS, MEASURES, validate


def _map_chunk(frame: pd.DataFrame, group_by: str) -> pd.DataFrame:
    validate(frame)
    return frame.groupby(group_by)[list(MEASURES)].sum().reset_index()


def mapreduce_analyze(
    path: str | Path, group_by: str = "platform", chunk_size: int = 100_000, workers: int = 2
) -> pd.DataFrame:
    if group_by not in DIMENSIONS:
        raise ValueError(f"group_by must be one of {DIMENSIONS}.")
    if workers < 1 or chunk_size < 1:
        raise ValueError("workers and chunk_size must be positive.")
    totals = None

    def reduce_partial(partial):
        nonlocal totals
        totals = (
            partial
            if totals is None
            else pd.concat([totals, partial]).groupby(group_by)[list(MEASURES)].sum().reset_index()
        )

    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = set()
        for frame in pd.read_csv(path, chunksize=chunk_size):
            pending.add(pool.submit(_map_chunk, frame, group_by))
            if len(pending) >= workers * 2:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    reduce_partial(future.result())
        for future in pending:
            reduce_partial(future.result())
    if totals is None:
        raise ValueError("Dataset must contain at least one row.")
    return with_kpis(totals.sort_values(group_by).reset_index(drop=True))
