"""Keep the checked-in terminal evidence tied to actual CLI output."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TerminalCaptureTests(unittest.TestCase):
    def test_casts_match_installed_cli(self):
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


if __name__ == "__main__":
    unittest.main()
