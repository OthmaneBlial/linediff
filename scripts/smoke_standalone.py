"""Exercise a frozen executable independently of the source package import path."""

import argparse
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = str(args.executable.resolve())
    with tempfile.TemporaryDirectory(prefix="linediff-smoke-") as directory:
        root = Path(directory)
        old = root / "old.py"
        new = root / "new.py"
        old.write_text(
            "def first():\n    return 1\n\ndef second():\n    return 2\n",
            encoding="utf-8",
        )
        new.write_text(
            "def second():\n    return 2\n\ndef first():\n    return 1\n",
            encoding="utf-8",
        )

        def check(arguments, expected_code, expected_output=b""):
            result = subprocess.run(
                [executable] + arguments,
                cwd=root,
                capture_output=True,
                timeout=30,
            )
            if (
                result.returncode != expected_code
                or expected_output not in result.stdout
            ):
                raise SystemExit(
                    "Standalone smoke failed for {}: code {}, stdout {!r}, stderr {!r}".format(
                        arguments,
                        result.returncode,
                        result.stdout[:500],
                        result.stderr[:500],
                    )
                )
            return result

        check(["--help"], 0, b"structural")
        check(["--check-only", str(old), str(new)], 1)
        check(["--check-only", str(old), str(old)], 0)
        check([str(old), str(new)], 0, b"--- ")
        check(["--display", "structural", str(old), str(new)], 0, b"MOVED first")
        fallback = check(
            ["--display", "structural", "--language", "json", str(old), str(new)],
            0,
            b"--- ",
        )
        if b"MOVED first" in fallback.stdout:
            raise SystemExit("Non-Python fallback unexpectedly used Python structure")
        check(
            ["sample.py", str(old), "oldhex", "100644", str(new), "newhex", "100644"],
            0,
            b"--- a/sample.py",
        )
    print(
        "PASS standalone help, exact diff, check-only, Python structure, fallback and Git operands"
    )


if __name__ == "__main__":
    main()
