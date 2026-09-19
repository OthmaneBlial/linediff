#!/usr/bin/env python3
"""Reproducible, read-only baseline for the bundled diff fixtures.

Run from the repository root: python scripts/benchmark.py
No files are written. Each engine measurement uses a fresh process so peak
resident memory is measured per case rather than across previous cases.
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tests" / "fixtures" / "cases.json"
SELECTED = ("replace", "moved_function", "signature_body", "long_line", "large")


def case_by_id(case_id):
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]
    return next(case for case in cases if case["id"] == case_id)


def worker(case_id):
    try:
        import resource
    except ImportError:
        resource = None

    sys.path.insert(0, str(ROOT / "src"))
    from linediff.diff import compute_diff

    case = case_by_id(case_id)
    with (ROOT / case["left"]).open("r", encoding="utf-8", newline="") as stream:
        left = stream.read()
    with (ROOT / case["right"]).open("r", encoding="utf-8", newline="") as stream:
        right = stream.read()

    started = time.perf_counter_ns()
    diff = compute_diff(left, right, case["left"], case["right"])
    engine_ms = (time.perf_counter_ns() - started) / 1_000_000
    rss_mib = None
    if resource is not None:
        raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mib = raw / (1024 * 1024) if sys.platform == "darwin" else raw / 1024
    print(json.dumps({"engine_ms": engine_ms, "peak_rss_mib": rss_mib, "lines": len(diff)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--worker", choices=SELECTED)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    if args.repeats < 1:
        parser.error("--repeats must be positive")

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(ROOT / "src")
    results = []
    for case_id in SELECTED:
        case = case_by_id(case_id)
        engine_times = []
        cli_times = []
        rss_values = []
        for _ in range(args.repeats):
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker", case_id],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            sample = json.loads(proc.stdout)
            engine_times.append(sample["engine_ms"])
            if sample["peak_rss_mib"] is not None:
                rss_values.append(sample["peak_rss_mib"])

            started = time.perf_counter_ns()
            cli = subprocess.run(
                [sys.executable, "-m", "linediff", "--check-only", case["left"], case["right"]],
                cwd=ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
            )
            cli_times.append((time.perf_counter_ns() - started) / 1_000_000)
            if cli.returncode not in (0, 1):
                raise RuntimeError("CLI failed for {}: {}".format(case_id, cli.stderr.decode(errors="replace")))

        results.append(
            {
                "id": case_id,
                "left_bytes": case["left_bytes"],
                "right_bytes": case["right_bytes"],
                "median_engine_ms": round(statistics.median(engine_times), 3),
                "median_cli_ms": round(statistics.median(cli_times), 3),
                "max_peak_rss_mib": round(max(rss_values), 2) if rss_values else None,
            }
        )

    revision = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    print(
        json.dumps(
            {
                "revision": revision,
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "repeats": args.repeats,
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
