#!/usr/bin/env python3
"""Check that four critical regression tests reject deliberate source faults.

This copies source and fixtures to a temporary directory. The working tree is
never mutated. Run after installing this checkout and pytest in the active
Python environment: python scripts/mutation_probe.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROBES = (
    (
        "final newline",
        "diff.py",
        "if left_content == right_content:",
        'if left_content.rstrip("\\n") == right_content.rstrip("\\n"):',
        "tests/test_exact_diff.py::ExactDiffTests::test_exact_change_detection",
    ),
    (
        "check-only exit code",
        "__main__.py",
        "return 0 if not diff_lines and not modes_differ and not names_differ else 1",
        "return 0 if not diff_lines and not modes_differ and not names_differ else 0",
        "tests/test_cli_contract.py::CliContractTests::test_check_only_distinguishes_same_change_and_error",
    ),
    (
        "forced language",
        "__main__.py",
        "lang = args.language or detect_language(git_path if git_mode else fromfile)",
        "lang = detect_language(git_path if git_mode else fromfile)",
        "tests/test_structural.py::StructuralTests::test_language_override_selects_python_view_for_text_extension",
    ),
    (
        "Python structural route",
        "__main__.py",
        'analyze_python_changes(content1, content2) if lang == "python" else None',
        "None",
        "tests/test_cli_contract.py::CliContractTests::test_diagnostics_identify_route_only_on_stderr",
    ),
)


def run_tests(directory, *nodes):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(directory / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="linediff-mutations-") as temporary:
        directory = Path(temporary)
        shutil.copytree(ROOT / "src" / "linediff", directory / "src" / "linediff")
        shutil.copytree(ROOT / "tests", directory / "tests")
        nodes = tuple(probe[4] for probe in PROBES)
        baseline = run_tests(directory, *nodes)
        if baseline.returncode:
            raise SystemExit(
                "Baseline tests failed:\n" + baseline.stdout + baseline.stderr
            )
        print("Baseline: {} targeted tests pass".format(len(nodes)))

        for label, filename, original, replacement, node in PROBES:
            source = directory / "src" / "linediff" / filename
            text = source.read_text(encoding="utf-8")
            if text.count(original) != 1:
                raise SystemExit("Mutation target is not unique: {}".format(label))
            source.write_text(text.replace(original, replacement, 1), encoding="utf-8")
            try:
                mutated = run_tests(directory, node)
            finally:
                source.write_text(text, encoding="utf-8")
            if mutated.returncode == 0 or "AssertionError" not in mutated.stdout:
                raise SystemExit(
                    "Mutation was not killed by its assertion: {}\n{}{}".format(
                        label, mutated.stdout, mutated.stderr
                    )
                )
            print("Killed: {} -> {}".format(label, node))


if __name__ == "__main__":
    main()
