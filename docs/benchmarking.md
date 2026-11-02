# Benchmark protocol

The required scale ladder is 10,000 → 100,000 → 1,000,000 → 10,000,000 rows.
`scripts/run_experiments.py` implements the entire ladder and checks each backend.
Files at each scale are generated independently from the same seed and chunk size.

## Comparable work

Each backend reads the same CSV, validates it, groups by platform, sums the same
five measures and derives the same KPIs. Spark also verifies the header against
its positional schema. Results are sorted by platform and compared within
`rtol=1e-9, atol=0.01` for the additive measures. The first successful run is the
parity reference; parity alone is not an independent correctness oracle, so tests
also verify known weighted KPI examples.

Runs use isolated child processes. Cold wall time includes Python imports, input
parsing, validation, aggregation, output serialization, and Spark startup/shutdown.
This is an end-to-end workload comparison. It is not a pure aggregation-kernel
microbenchmark or a warm distributed-cluster comparison.

## Recorded values

- `seconds`: measured wall-clock time, including startup and I/O.
- `peak_tree_rss_mb`: maximum sampled sum of parent/child resident memory every 20 ms.
- `status`: ok, error, timeout or mismatch.
- `parity`: whether grouped numeric totals match the first successful output.
- `environment.json`: Python, OS, CPU, RAM, workers, chunk size and timing convention.
- Per-run CSV and log files for diagnosis and reproducibility.

RSS samples may miss brief spikes, include shared pages more than once, and exclude
remote executor memory. They are approximate local process-tree measurements, not
precise exclusive memory or cluster memory. Benchmark backends run in fixed order;
OS filesystem caching can favor later runs. There is no cache eviction or warmup.
Interpret medians across at least three repeats alongside these limits.

## Reproduce

```bash
python scripts/run_experiments.py --repeats 3
# Smaller smoke run, no Java:
python scripts/run_experiments.py --sizes 10000 100000 --backends pandas mapreduce --repeats 1
```

Use the same machine and record changes to Java, Python and package versions.
Avoid heavy concurrent workloads. Inspect failures before comparing speeds.
Do not infer a universal winner from one machine or one scale. Checked-in results
must identify which scales were actually executed; the full ladder command is
provided even when local resource limits prevent a complete run.
