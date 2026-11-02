# Digital Advertising Budget Optimizer project report

## Objective

Help a marketing manager decide how to distribute the next PKR 1 million across
five advertising platforms, using simulated historical data. Demonstrate how the
same analytics can be executed with Pandas, local MapReduce and Spark, and how
computational cost changes as data volume increases.

## Requirement coverage

| Brief requirement | Implementation |
| --- | --- |
| Facebook, Instagram, Google, TikTok and YouTube | Shared platform contract and simulator |
| Date, campaign, funnel, revenue and audience fields | Twelve-column validated CSV schema |
| CTR, CPC, CPA, conversion rate and ROAS | Weighted aggregate analytics |
| Revenue and campaign performance | CLI grouping and dashboard segment comparisons |
| 10,000 to 10 million rows | Chunked generator and four-scale experiment runner |
| Pandas versus MapReduce versus Spark | Separate real backends and isolated parity benchmarks |
| Marketing budget recommendation engine | Constrained, revenue-oriented scenario allocator |
| Management-facing result | Interactive dashboard and downloadable CSV plan |

## Deliverables

The repository includes the source package, CLI, dashboard, sample data, measured
sample outputs, automated tests, CI, container setup, data dictionary, allocation
methodology and benchmark protocol. The original brief is treated as project
requirements, not as instructions to copy unrelated external projects.

## Analysis and recommendation

The committed sample outputs show each platform's funnel totals and weighted
KPIs. A recommendation assigns the next budget subject to default 5% floors and
45% caps. Its exact distribution is calculated from the supplied history; the
example percentages in the brief are illustrative rather than fixed answers.
All five platforms, including YouTube, remain eligible when present in the data.

The model shrinks sparse ROAS estimates and applies assumed diminishing returns.
The result supports discussion of plausible allocations and sensitivity to
constraints. It should be evaluated through controlled experiments before a
real-world spending decision.

## Experimental evidence

Measured outputs and the execution environment are stored under
`examples/results/`. Benchmark statuses distinguish successful results from failed
or unavailable backends. Tests cover deterministic generation, funnel validation,
weighted KPIs, backend parity, budget conservation, feasibility and CLI workflows.
Spark integration has a dedicated Java-enabled CI job.

The execution record in `examples/results/README.md` identifies the scales and
backends actually run during preparation. The full four-scale runner is included
for reproducing or extending the experiment on an appropriately sized machine.

## Limitations and extensions

The data is simulated and its platform differences are authored assumptions.
Local MapReduce is not a distributed Hadoop deployment. Spark benchmarks on one
machine do not demonstrate cluster scaling. Attributed revenue is not incremental
profit. Response curves are scenario assumptions, not fitted causal estimates.

Useful extensions include time-based evaluation, incrementality experiments,
margin-aware allocation, learned saturation curves, and Parquet/object-storage
inputs for distributed processing. These require evidence and infrastructure
beyond the supplied brief; they are not represented as implemented features.
