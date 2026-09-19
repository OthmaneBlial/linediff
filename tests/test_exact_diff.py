"""Byte-preserving text diff checks against the frozen fixture corpus."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from linediff.render import format_unified_diff
from linediff.diff import compute_diff


ROOT = Path(__file__).resolve().parent.parent
CASES = json.loads(
    (ROOT / "tests" / "fixtures" / "cases.json").read_text(encoding="utf-8")
)["cases"]


class ExactDiffTests(unittest.TestCase):
    def test_exact_change_detection(self):
        for case in CASES:
            if case["kind"] == "binary":
                continue
            with self.subTest(case=case["id"]):
                old_bytes = (ROOT / case["left"]).read_bytes()
                new_bytes = (ROOT / case["right"]).read_bytes()
                old = old_bytes.decode("utf-8")
                new = new_bytes.decode("utf-8")
                self.assertEqual(bool(compute_diff(old, new)), old_bytes != new_bytes)

                env = os.environ.copy()
                env["PYTHONDONTWRITEBYTECODE"] = "1"
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "linediff",
                        "--check-only",
                        case["left"],
                        case["right"],
                    ],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 1 if old_bytes != new_bytes else 0)
                self.assertEqual(result.stdout, b"")

    @unittest.skipUnless(shutil.which("git"), "git is required for patch round-trips")
    def test_unified_patches_apply_to_exact_source_bytes(self):
        for case in CASES:
            if case["kind"] == "binary":
                continue
            with self.subTest(case=case["id"]):
                old_bytes = (ROOT / case["left"]).read_bytes()
                new_bytes = (ROOT / case["right"]).read_bytes()
                records = compute_diff(
                    old_bytes.decode("utf-8"), new_bytes.decode("utf-8")
                )
                if old_bytes == new_bytes:
                    self.assertEqual(records, [])
                    continue

                patch = format_unified_diff(records, "source.txt", "source.txt") + "\n"
                self.assertEqual(patch.count("--- source.txt"), 1)
                self.assertEqual(patch.count("+++ source.txt"), 1)
                if case["id"] == "final_newline":
                    self.assertIn("\\ No newline at end of file", patch)

                with tempfile.TemporaryDirectory() as directory:
                    source = Path(directory) / "source.txt"
                    source.write_bytes(old_bytes)
                    applied = subprocess.run(
                        ["git", "apply", "-"],
                        cwd=directory,
                        input=patch.encode("utf-8"),
                        capture_output=True,
                    )
                    self.assertEqual(
                        applied.returncode, 0, applied.stderr.decode(errors="replace")
                    )
                    self.assertEqual(source.read_bytes(), new_bytes)


if __name__ == "__main__":
    unittest.main()
