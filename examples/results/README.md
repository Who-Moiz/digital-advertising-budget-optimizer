# Execution record

Prepared on 2026-11-02 using Python 3.12.8, Pandas 2.3.3, PySpark 3.5.9 and Java 17
on Windows with approximately 15.7 GiB RAM. Package versions are captured in
`requirements-lock.txt` and per-scale environment files. All data is synthetic.

## Completed validation

- 29 tests passed, including Spark integration and dashboard interactions.
- Ruff lint and formatting checks passed.
- `pip check` found no broken dependency requirements.
- Pandas, local MapReduce and Spark completed at 10,000, 100,000, 1 million and
  10 million rows; all grouped platform totals matched within documented tolerances.

## Sample recommendation

The committed `data/sample/campaigns.csv` contains 10,000 records generated with
seed 42 and chunk size 100,000. Its default next-budget recommendation is:

| Platform | Allocation (PKR) | Share |
| --- | ---: | ---: |
| Facebook | 122,500 | 12.25% |
| Google | 450,000 | 45.00% |
| Instagram | 184,400 | 18.44% |
| TikTok | 161,200 | 16.12% |
| YouTube | 81,900 | 8.19% |
| Total | 1,000,000 | 100.00% |

These percentages are the output of an assumed response model using simulated
data. They are not general recommendations for these advertising platforms.

## Benchmark evidence

| Rows | Pandas seconds | MapReduce seconds | Spark seconds | Totals match |
| ---: | ---: | ---: | ---: | :---: |
| 10,000 | 1.39 | 3.01 | 31.00 | Yes |
| 100,000 | 2.99 | 4.68 | 53.34 | Yes |
| 1,000,000 | 5.10 | 5.19 | 51.21 | Yes |
| 10,000,000 | 123.11 | 50.28 | 93.16 | Yes |

| Rows | Pandas RSS MiB | MapReduce RSS MiB | Spark RSS MiB |
| ---: | ---: | ---: | ---: |
| 10,000 | 83.24 | 159.00 | 494.76 |
| 100,000 | 109.15 | 189.88 | 512.90 |
| 1,000,000 | 398.13 | 370.21 | 592.95 |
| 10,000,000 | 3,287.03 | 411.41 | 692.12 |

The `benchmarks/<rows>/` directories contain actual per-backend KPI outputs,
timing/memory CSVs and sanitized environment metadata. The 10-million-row input
occupied 932,782,706 bytes. Large raw datasets remain local and are reproducible
using the experiment runner; they are intentionally excluded from the repository.

Each value is a **single cold run**, not a repeated-run median. Some measurements
overlapped with other project validation and backend runs. Filesystem caches were
not cleared and backend ordering was fixed. These numbers demonstrate successful
execution and local resource use; they do not establish a controlled speed ranking.
Memory is 20 ms sampled aggregate process-tree RSS, including the Spark JVM when
visible, and may double count shared pages or miss short spikes.

Use `python scripts/run_experiments.py --repeats 3` on an otherwise idle machine
for a more defensible performance comparison. Read the full
[benchmark protocol](../../docs/benchmarking.md) before interpreting results.
