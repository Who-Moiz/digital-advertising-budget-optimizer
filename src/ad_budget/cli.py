"""Command-line workflow for data generation, analytics, allocation and benchmarks."""

import argparse
from pathlib import Path

from ad_budget.analytics import chunked_analyze, pandas_analyze
from ad_budget.benchmark import benchmark
from ad_budget.generate import generate_csv
from ad_budget.mapreduce import mapreduce_analyze
from ad_budget.optimizer import recommend
from ad_budget.schema import DIMENSIONS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Digital Advertising Budget Optimizer")
    commands = parser.add_subparsers(dest="command", required=True)
    gen = commands.add_parser("generate", help="Generate synthetic CSV data")
    gen.add_argument("--rows", type=int, default=10_000)
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--chunk-size", type=int, default=100_000)
    gen.add_argument("--output", default="data/generated/campaigns_10000.csv")
    analyze = commands.add_parser("analyze", help="Calculate weighted marketing KPIs")
    analyze.add_argument("input")
    analyze.add_argument(
        "--backend", choices=["pandas", "chunked", "mapreduce", "spark"], default="pandas"
    )
    analyze.add_argument("--group-by", choices=DIMENSIONS, default="platform")
    analyze.add_argument("--chunk-size", type=int, default=100_000)
    analyze.add_argument("--workers", type=int, default=2)
    analyze.add_argument("--output", default="artifacts/platform_performance.csv")
    optimize = commands.add_parser("recommend", help="Allocate a future PKR budget")
    optimize.add_argument("input", help="Raw advertising CSV")
    optimize.add_argument("--budget", type=float, default=1_000_000)
    optimize.add_argument("--min-share", type=float, default=0.05)
    optimize.add_argument("--max-share", type=float, default=0.45)
    optimize.add_argument("--prior-strength", type=float, default=50_000)
    optimize.add_argument("--saturation", type=float, default=0.75)
    optimize.add_argument("--output", default="artifacts/budget_recommendations.csv")
    bench = commands.add_parser("benchmark", help="Benchmark in isolated child processes")
    bench.add_argument("input")
    bench.add_argument(
        "--backends",
        nargs="+",
        choices=["pandas", "chunked", "mapreduce", "spark"],
        default=["pandas", "mapreduce", "spark"],
    )
    bench.add_argument("--repeats", type=int, default=3)
    bench.add_argument("--chunk-size", type=int, default=100_000)
    bench.add_argument("--workers", type=int, default=2)
    bench.add_argument("--timeout", type=float, default=1800)
    bench.add_argument("--output", default="artifacts/benchmark")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            generate_csv(args.output, args.rows, args.seed, args.chunk_size)
            print(f"Generated {args.rows:,} synthetic rows: {args.output}")
            return
        if args.command == "analyze":
            if args.backend == "pandas":
                result = pandas_analyze(args.input, args.group_by)
            elif args.backend == "chunked":
                result = chunked_analyze(args.input, args.group_by, args.chunk_size)
            elif args.backend == "mapreduce":
                result = mapreduce_analyze(args.input, args.group_by, args.chunk_size, args.workers)
            else:
                from ad_budget.spark import spark_analyze

                result = spark_analyze(args.input, args.group_by)
        elif args.command == "recommend":
            result = recommend(
                chunked_analyze(args.input),
                args.budget,
                args.min_share,
                args.max_share,
                args.prior_strength,
                args.saturation,
            )
        else:
            result = benchmark(
                args.input,
                args.output,
                args.backends,
                args.repeats,
                args.chunk_size,
                args.workers,
                args.timeout,
            )
            print(result.to_string(index=False))
            if not result.status.eq("ok").all():
                parser.exit(1, f"Some backends failed; inspect logs in {args.output}.\n")
            return
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)
        print(result.to_string(index=False))
        print(f"Saved: {args.output}")
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")
