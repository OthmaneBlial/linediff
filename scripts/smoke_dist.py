#!/usr/bin/env python3
"""Install every built distribution outside the checkout and exercise its CLI."""

import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def run(arguments, cwd):
    result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "{} failed ({}): {}".format(arguments, result.returncode, result.stderr)
        )
    return result


def main():
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
    artifacts = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    if len(artifacts) != 2:
        raise RuntimeError("Expected one wheel and one sdist in {}".format(directory))
    for artifact in artifacts:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = root / "venv"
            venv.EnvBuilder(with_pip=True).create(environment)
            executable = environment / (
                "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
            )
            run(
                [str(executable), "-m", "pip", "install", "--no-deps", str(artifact)],
                root,
            )
            help_result = run([str(executable), "-m", "linediff", "--help"], root)
            if "--display" not in help_result.stdout:
                raise RuntimeError("Missing CLI options in {}".format(artifact.name))
            old = root / "old.py"
            new = root / "new.py"
            old.write_text("def total(x):\n    return x\n", encoding="utf-8")
            new.write_text("def total(x):\n    return x + 1\n", encoding="utf-8")
            changed = subprocess.run(
                [str(executable), "-m", "linediff", "--check-only", str(old), str(new)],
                cwd=root,
            )
            if changed.returncode != 1:
                raise RuntimeError(
                    "Incorrect change exit status in {}".format(artifact.name)
                )
            structural = run(
                [
                    str(executable),
                    "-m",
                    "linediff",
                    "--display",
                    "structural",
                    str(old),
                    str(new),
                ],
                root,
            )
            if (
                "CHANGED total (body)" not in structural.stdout
                or "Exact text diff:" not in structural.stdout
            ):
                raise RuntimeError(
                    "Structural smoke failed in {}".format(artifact.name)
                )
            print("PASS {}".format(artifact.name))


if __name__ == "__main__":
    main()
