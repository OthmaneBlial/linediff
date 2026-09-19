"""Keep the checked-in terminal evidence tied to actual CLI output."""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TerminalCaptureTests(unittest.TestCase):
    def test_casts_match_installed_cli(self):
        for name in ("move_a.py", "move_b.py"):
            self.assertNotIn(b"\r", (ROOT / "data" / name).read_bytes())
        cases = (
            ("structural", ("--display", "structural"), (60, 18)),
            (
                "columns",
                ("--display", "side-by-side", "--width", "80", "--color", "always"),
                (80, 16),
            ),
            ("inline", ("--display", "inline", "--color", "always"), (60, 18)),
        )
        for name, options, geometry in cases:
            with self.subTest(name=name):
                cast = ROOT / "assets" / "casts" / (name + "-output.cast")
                records = [
                    json.loads(line)
                    for line in cast.read_text(encoding="utf-8").splitlines()
                ]
                self.assertEqual((records[0]["width"], records[0]["height"]), geometry)
                captured = "".join(event[2] for event in records[1:] if event[1] == "o")
                captured = captured.replace("\r\n", "\n")
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "linediff",
                        *options,
                        "data/move_a.py",
                        "data/move_b.py",
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(captured, result.stdout)
                if name == "structural":
                    self.assertIn("MOVED calculate_total", captured)

    @unittest.skipUnless(shutil.which("git"), "git is required for Git capture")
    def test_git_cast_matches_real_external_diff(self):
        cast = ROOT / "assets" / "casts" / "git-output.cast"
        records = [
            json.loads(line) for line in cast.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual((records[0]["width"], records[0]["height"]), (60, 17))
        captured = "".join(event[2] for event in records[1:] if event[1] == "o")
        captured = captured.replace("\r\n", "\n")
        with tempfile.TemporaryDirectory() as directory:
            old = (ROOT / "data" / "move_a.py").read_bytes()
            new = (ROOT / "data" / "move_b.py").read_bytes()
            target = Path(directory) / "calc.py"
            target.write_bytes(old)
            subprocess.run(["git", "init", "-q"], cwd=directory, check=True)
            subprocess.run(
                ["git", "config", "core.autocrlf", "false"], cwd=directory, check=True
            )
            subprocess.run(["git", "add", "calc.py"], cwd=directory, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Linediff Demo",
                    "-c",
                    "user.email=demo@example.invalid",
                    "commit",
                    "-qm",
                    "baseline",
                ],
                cwd=directory,
                check=True,
            )
            target.write_bytes(new)
            command = shlex.quote(sys.executable) + " -m linediff --display structural"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                ["git", "-c", "diff.external=" + command, "diff", "--ext-diff"],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(captured, result.stdout.replace("\r\n", "\n"))
            self.assertIn("MOVED calculate_total", captured)
            self.assertIn("--- a/calc.py", captured)


if __name__ == "__main__":
    unittest.main()
