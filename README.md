# Digital Advertising Budget Optimizer

[![CI](https://github.com/Who-Moiz/digital-advertising-budget-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/Who-Moiz/digital-advertising-budget-optimizer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%20%E2%80%93%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Where should a company spend its next Rs. 1 million?** This project turns campaign
history into weighted marketing KPIs and a constrained budget scenario across
Facebook, Instagram, Google, TikTok, and YouTube. It also compares Pandas, a local
MapReduce implementation, and Apache Spark at increasing dataset sizes.

All bundled data is **synthetic**, denominated in **Pakistani rupees (PKR)**. Platform
differences are simulation assumptions. Recommendations are decision-support scenarios,
not causal forecasts or promises of return.

## Features

- Seeded, bounded-memory CSV generation at 10,000, 100,000, 1 million and 10 million rows.
- CTR, CPC, CPA, conversion rate, ROAS, revenue and campaign/audience analysis.
- Four analysis modes: in-memory Pandas, chunked Pandas, process-based MapReduce, Spark SQL.
- Isolated benchmark runs with elapsed time, sampled process-tree RSS, failure logs and parity checks.
- Budget allocation with platform floors/caps, sparse-data shrinkage and diminishing returns.
- Streamlit dashboard with filters, campaign comparisons, adjustable scenarios and CSV exports.
- Automated tests, cross-platform CI, Spark integration CI, container setup and contribution guides.

## Quick start

Install Python 3.11 or 3.12, then run from this repository:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
python -m pip install -e ".[dashboard,dev]"
python -m ad_budget generate --rows 10000
python -m ad_budget analyze data/generated/campaigns_10000.csv
python -m ad_budget recommend data/generated/campaigns_10000.csv --budget 1000000
python -m streamlit run dashboard/app.py
```

The dashboard opens with the committed 10,000-row sample. Upload a CSV using the
[data contract](docs/data_dictionary.md), or use generated data from the CLI. Dashboard
uploads are capped at 200,000 rows; use the CLI for the larger experiments.

On Windows, `powershell -ExecutionPolicy Bypass -File scripts/start_dashboard.ps1`
also launches the dashboard using an existing `.venv` or project-local runtime.
For an exact dependency snapshot from the validation environment, install
`requirements-lock.txt` before `pip install --no-deps -e .`; the snapshot includes
dashboard, development and Spark packages. The normal editable install above
resolves compatible versions for your platform.

### Apache Spark

Install **Java 17**, set `JAVA_HOME`, and install the optional dependency:

```bash
python -m pip install -e ".[spark]"
python -m ad_budget analyze data/sample/campaigns.csv --backend spark
```

Spark defaults to two local workers. The implementation uses an explicit schema,
distributed validation and SQL aggregation. For a reproducible Spark environment,
use the included Docker image; on Windows, Docker or WSL is recommended if native
Spark encounters Hadoop/Java setup problems.

### Run the full scale comparison

```bash
python scripts/run_experiments.py --sizes 10000 100000 1000000 10000000 --repeats 3
```

This generates each dataset and benchmarks Pandas, MapReduce and Spark. Results live
in `artifacts/experiments/<size>/`. Start small: the 10-million-row CSV can consume
several GB on disk, and full Pandas loading needs considerably more memory. Backends
have a configurable timeout; failures are recorded and never presented as successes.

```bash
# A quick comparison without Java:
python -m ad_budget benchmark data/sample/campaigns.csv --backends pandas mapreduce --repeats 3
# Memory-conscious analysis:
python -m ad_budget analyze data/generated/campaigns_1000000.csv --backend chunked
# Campaign ranking:
python -m ad_budget analyze data/sample/campaigns.csv --group-by campaign
# Custom allocation constraints (fractions, not percentages):
python -m ad_budget recommend data/sample/campaigns.csv --min-share 0.05 --max-share 0.40
```

## Repository structure

```text
├── src/ad_budget/          # Validated analytics, generation, allocation and CLI
│   ├── schema.py          # Shared data contract
│   ├── generate.py        # Synthetic funnel simulation
│   ├── analytics.py       # Pandas and chunked KPIs
│   ├── mapreduce.py       # Parallel map / bounded local reduce
│   ├── spark.py           # Spark SQL backend
│   ├── optimizer.py       # Constrained scenario allocation
│   ├── benchmark.py       # Isolated benchmark harness
│   └── cli.py             # Command-line entry point
├── dashboard/app.py       # Interactive Streamlit application
├── data/sample/           # Small committed synthetic dataset
├── data/generated/        # Ignored larger experiment datasets
├── examples/results/      # Reproducible sample outputs and measured results
├── scripts/               # Experiment automation
├── tests/                 # Unit, parity and integration tests
├── docs/                  # Methodology, architecture and project report
├── artifacts/             # Ignored local outputs
├── .github/               # CI, issues and pull request templates
├── Dockerfile
└── pyproject.toml
```

## Methodology

KPIs are computed from **sums**, not averages of row ratios. For example,
`CTR = 100 × sum(clicks) / sum(impressions)`. A zero denominator produces an
undefined value (blank in CSV), never an invented zero or infinity.

The allocator shrinks each platform's historical ROAS toward overall ROAS and
assigns discrete budget increments by modeled marginal revenue. A concave log
response discourages unlimited concentration. The full budget is conserved to
the paisa, with explicit feasibility checks for share constraints. See
[allocation methodology](docs/methodology.md) for the response formula and limitations.

Local MapReduce demonstrates map/combine/reduce and multiprocessing. It is **not
a Hadoop cluster**. Spark runs locally by default; local benchmarks measure overhead
and scaling on one machine, not distributed-cluster speedups.

## Validation and results

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
# Explicit Spark integration run (requires optional dependency + Java):
python -m pytest -q tests/test_spark.py
```

See [the project report](docs/project_report.md) for requirement coverage and the
[results directory](examples/results/) for actual outputs. Benchmark files include
machine metadata and status per run; only successful, matching outputs should be
compared. No unexecuted scale is represented as a measured result.

All three required backends were executed at **all four scales**, through
**10 million rows**, and their platform totals matched. Local validation passed
**29 tests**, including Spark and dashboard workflows. The measured runs are
single-run demonstrations; see [the execution record](examples/results/README.md)
for timings, memory and experimental limitations.

## Container

```bash
docker build -t ad-budget .
docker run --rm -p 8501:8501 ad-budget
# Analytics command in the same Java-enabled image:
docker run --rm ad-budget python -m ad_budget analyze data/sample/campaigns.csv --backend spark
```

## Documentation and contribution

- [Data dictionary](docs/data_dictionary.md)
- [Architecture and operations](docs/architecture.md)
- [KPI and recommendation methodology](docs/methodology.md)
- [Benchmark protocol](docs/benchmarking.md)
- [Project report](docs/project_report.md)
- [Technical references](docs/references.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

Released under the [MIT license](LICENSE).
