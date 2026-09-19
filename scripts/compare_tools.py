#!/usr/bin/env python3
"""Record a dated, local-only comparison against Git, Difftastic and delta.

Run with installed official competitor binaries. This script writes raw outputs
and small-case timings; it makes no superiority claim and installs nothing.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
CASES = ("moved_function", "signature_body", "format_only", "final_newline")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def execute(command, environment):
    started = time.perf_counter_ns()
    result = subprocess.run(
        command,
        cwd=FIXTURES,
        env=environment,
        capture_output=True,
        timeout=15,
        check=False,
    )
    duration = (time.perf_counter_ns() - started) / 1_000_000
    if result.returncode not in (0, 1):
        raise RuntimeError(
            "{} exited {}: {}".format(
                command[0], result.returncode, result.stderr.decode("utf-8", "replace")
            )
        )
    return result, duration


def version(command):
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=True
    )
    return (result.stdout or result.stderr).splitlines()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--difft", type=Path, required=True)
    parser.add_argument("--delta", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    args.difft = args.difft.resolve()
    args.delta = args.delta.resolve()
    declared = re.search(
        r'(?m)^version = "([^"]+)"$',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    installed = version(
        [
            sys.executable,
            "-c",
            "from importlib.metadata import version; print(version('linediff'))",
        ]
    )
    if declared is None or installed != declared.group(1):
        parser.error("installed Linediff version does not match this checkout")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        parser.error("--out-dir must be empty")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "NO_COLOR": "1",
            "TERM": "dumb",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    metadata = {
        "date": date.today().isoformat(),
        "revision": version(["git", "rev-parse", "--short", "HEAD"]),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "repeats": args.repeats,
        "versions": {
            "git": version(["git", "--version"]),
            "linediff": installed,
            "difftastic": version([str(args.difft), "--version"]),
            "delta": version([str(args.delta), "--version"]),
        },
        "cases": [],
    }
    for case in CASES:
        suffix = ".txt" if case == "final_newline" else ".py"
        left, right = case + ".old" + suffix, case + ".new" + suffix
        commands = {
            "git": [
                "git",
                "--no-pager",
                "diff",
                "--no-index",
                "--no-ext-diff",
                "--no-color",
                "--",
                left,
                right,
            ],
            "linediff": [
                sys.executable,
                "-m",
                "linediff",
                "--display",
                "structural",
                left,
                right,
            ],
            "difftastic": [
                str(args.difft),
                "--color",
                "never",
                "--display",
                "inline",
                "--width",
                "80",
                left,
                right,
            ],
            "delta": [
                str(args.delta),
                "--paging",
                "never",
                "--no-gitconfig",
                "--width",
                "80",
                left,
                right,
            ],
        }
        entry = {"id": case, "inputs": {}, "tools": {}}
        for name in (left, right):
            entry["inputs"][name] = hashlib.sha256(
                (FIXTURES / name).read_bytes()
            ).hexdigest()
        for tool, command in commands.items():
            execute(command, environment)  # warm-up is excluded from the median
            durations = []
            for _ in range(args.repeats):
                result, duration = execute(command, environment)
                durations.append(duration)
            stdout = result.stdout.decode("utf-8")
            stderr = result.stderr.decode("utf-8")
            output_name = "{}.{}.txt".format(case, tool)
            if tool == "delta":
                (args.out_dir / "{}.delta.ansi".format(case)).write_bytes(result.stdout)
                stdout = ANSI.sub("", stdout)
            (args.out_dir / output_name).write_text(stdout, encoding="utf-8")
            entry["tools"][tool] = {
                "exit_code": result.returncode,
                "median_wall_ms": round(statistics.median(durations), 3),
                "output": output_name,
                "stderr": stderr,
            }
        metadata["cases"].append(entry)
    (args.out_dir / "results.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print("Recorded {} cases in {}".format(len(CASES), args.out_dir))


if __name__ == "__main__":
    main()
