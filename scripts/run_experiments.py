"""Generate and benchmark the four dataset sizes specified in the project brief."""

import argparse
from pathlib import Path

from ad_budget.benchmark import benchmark
from ad_budget.generate import generate_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[10_000, 100_000, 1_000_000, 10_000_000]
    )
    parser.add_argument("--backends", nargs="+", default=["pandas", "mapreduce", "spark"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args()
    failed = False
    for size in args.sizes:
        path = Path(f"data/generated/campaigns_{size}.csv")
        print(f"Generating {size:,} rows", flush=True)
        generate_csv(path, size, chunk_size=args.chunk_size)
        result = benchmark(
            path,
            f"artifacts/experiments/{size}",
            args.backends,
            args.repeats,
            args.chunk_size,
            args.workers,
            args.timeout,
        )
        print(result.to_string(index=False), flush=True)
        failed = failed or not result.status.eq("ok").all()
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
