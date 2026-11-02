import json

import pandas as pd

from ad_budget.benchmark import benchmark
from ad_budget.cli import main


def test_cli_end_to_end(tmp_path):
    data = tmp_path / "data.csv"
    kpis = tmp_path / "kpis.csv"
    plan = tmp_path / "plan.csv"
    main(["generate", "--rows", "50", "--output", str(data)])
    main(["analyze", str(data), "--output", str(kpis)])
    main(["recommend", str(data), "--output", str(plan)])
    assert len(pd.read_csv(kpis)) == 5
    assert pd.read_csv(plan).recommended_budget.sum() == 1_000_000


def test_benchmark_records_actual_results(tmp_path):
    data = tmp_path / "data.csv"
    main(["generate", "--rows", "50", "--output", str(data)])
    output = tmp_path / "bench"
    result = benchmark(data, output, ["pandas", "mapreduce"], repeats=1, chunk_size=25)
    assert result.status.eq("ok").all()
    assert result.parity.all()
    assert result.seconds.gt(0).all()
    assert result.peak_tree_rss_mb.gt(0).all()
    assert json.loads((output / "environment.json").read_text())["repeats"] == 1
