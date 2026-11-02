"""Isolated-process timing, sampled process-tree memory, and parity checks."""

import json
import os
import platform
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

from ad_budget.schema import MEASURES


def _memory_bytes(process):
    total = 0
    try:
        family = [process, *process.children(recursive=True)]
    except psutil.Error:
        return 0
    for member in family:
        try:
            total += member.memory_info().rss
        except psutil.Error:
            pass
    return total


def benchmark(
    path,
    output,
    backends=("pandas", "mapreduce", "spark"),
    repeats=3,
    chunk_size=100_000,
    workers=2,
    timeout=1800,
):
    """Time cold processes, including imports, validation, I/O and Spark startup."""
    if repeats < 1 or timeout <= 0:
        raise ValueError("repeats and timeout must be positive.")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    reference = None
    for backend in backends:
        if backend not in ("pandas", "mapreduce", "spark", "chunked"):
            raise ValueError(f"Unsupported backend: {backend}")
        for repeat in range(1, repeats + 1):
            result = output / f"{backend}_{repeat}.csv"
            log = output / f"{backend}_{repeat}.log"
            result.unlink(missing_ok=True)
            command = [
                sys.executable,
                "-m",
                "ad_budget",
                "analyze",
                str(path),
                "--backend",
                backend,
                "--output",
                str(result),
                "--chunk-size",
                str(chunk_size),
                "--workers",
                str(workers),
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = (
                str(Path(__file__).resolve().parents[1]) + os.pathsep + env.get("PYTHONPATH", "")
            )
            start = time.perf_counter()
            peak = 0
            timed_out = False
            with log.open("w", encoding="utf-8") as handle:
                child = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, env=env)
                monitored = psutil.Process(child.pid)
                while child.poll() is None:
                    peak = max(peak, _memory_bytes(monitored))
                    if time.perf_counter() - start > timeout:
                        timed_out = True
                        try:
                            descendants = monitored.children(recursive=True)
                        except psutil.Error:
                            descendants = []
                        for member in reversed(descendants):
                            try:
                                member.kill()
                            except psutil.Error:
                                pass
                        child.kill()
                        child.wait()
                        break
                    time.sleep(0.02)
            elapsed = time.perf_counter() - start
            status = "timeout" if timed_out else "ok" if child.returncode == 0 else "error"
            parity = False
            if status == "ok":
                values = pd.read_csv(result).sort_values("platform").reset_index(drop=True)
                if reference is None:
                    reference = values
                parity = values.platform.equals(reference.platform) and np.allclose(
                    values[list(MEASURES)], reference[list(MEASURES)], rtol=1e-9, atol=0.01
                )
                if not parity:
                    status = "mismatch"
            records.append(
                {
                    "backend": backend,
                    "repeat": repeat,
                    "status": status,
                    "seconds": elapsed,
                    "peak_tree_rss_mb": peak / 1024**2,
                    "parity": parity,
                    "input_bytes": Path(path).stat().st_size,
                }
            )
            pd.DataFrame(records).to_csv(output / "benchmark.csv", index=False)
    packages = {}
    for package in ("numpy", "pandas", "psutil", "pyspark", "streamlit"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            pass
    metadata = {
        "python": sys.version,
        "packages": packages,
        "os": platform.platform(),
        "cpu": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "ram_gb": psutil.virtual_memory().total / 1024**3,
        "chunk_size": chunk_size,
        "workers": workers,
        "repeats": repeats,
        "input": str(Path(path).resolve()),
        "timing": "cold end-to-end wall time",
        "memory": "20ms sampled sum of parent and descendant RSS; shared pages may repeat",
    }
    (output / "environment.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return pd.DataFrame(records)
