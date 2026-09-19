"""CLI exit codes and input preservation, independent of display snapshots."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(ROOT / "src")
ENV["PYTHONDONTWRITEBYTECODE"] = "1"


def run_cli(*arguments, input_bytes=None, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-m", "linediff"] + list(arguments),
        input=input_bytes,
        cwd=cwd,
        env=ENV,
        capture_output=True,
    )


class CliContractTests(unittest.TestCase):
    def test_check_only_distinguishes_same_change_and_error(self):
        old = "tests/fixtures/final_newline.old.txt"
        new = "tests/fixtures/final_newline.new.txt"
        self.assertEqual(run_cli("--check-only", old, old).returncode, 0)
        changed = run_cli("--check-only", old, new)
        self.assertEqual(changed.returncode, 1)
        self.assertEqual(changed.stdout, b"")
        missing = run_cli("--check-only", old, "missing-file.txt")
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(missing.stdout, b"")
        self.assertIn(b"Cannot read", missing.stderr)

    def test_bad_file_inputs_report_error_without_traceback(self):
        for path, message in (
            ("tests/fixtures/binary.old.bin", b"Cannot decode"),
            ("tests/fixtures", b"Cannot read"),
        ):
            with self.subTest(path=path):
                result = run_cli("--check-only", path, "tests/fixtures/replace.new.txt")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(message, result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory, "binary.dat")
            binary.write_bytes(b"abc\x00def")
            result = run_cli("--check-only", str(binary), "tests/fixtures/replace.new.txt")
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"Binary", result.stderr)

    def test_stdin_pair_preserves_final_newline_and_crlf(self):
        for pair in (b"alpha\n---\nalpha", b"alpha\r\n---\r\nalpha\n"):
            with self.subTest(pair=pair):
                result = run_cli("--check-only", input_bytes=pair)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
        same = run_cli("--check-only", input_bytes=b"alpha\n---\nalpha\n")
        self.assertEqual(same.returncode, 0)

    def test_stdin_rejects_git_patch_and_invalid_bytes(self):
        for payload in (b"--- a/file\n+++ b/file\n@@ -1 +1 @@\n-a\n+b\n", b"\xff\n---\nabc"):
            with self.subTest(payload=payload):
                result = run_cli(input_bytes=payload)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"Error:", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)

    def test_dash_prefixed_names_work_after_double_dash(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "-old.txt").write_text("old\n", encoding="utf-8")
            Path(directory, "-new.txt").write_text("new\n", encoding="utf-8")
            result = run_cli("--check-only", "--", "-old.txt", "-new.txt", cwd=directory)
            self.assertEqual(result.returncode, 1, result.stderr.decode(errors="replace"))

    def test_unknown_language_is_a_usage_error(self):
        result = run_cli(
            "--language", "unknown-grammar", "tests/fixtures/replace.old.txt",
            "tests/fixtures/replace.new.txt",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"invalid choice", result.stderr)

    def test_closed_output_pipe_does_not_print_traceback(self):
        process = subprocess.Popen(
            [sys.executable, "-m", "linediff", "tests/fixtures/long_line.old.txt", "tests/fixtures/long_line.new.txt"],
            cwd=ROOT,
            env=ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.stdout.close()
        stderr = process.stderr.read()
        self.assertEqual(process.wait(timeout=10), 0, stderr.decode(errors="replace"))
        self.assertNotIn(b"Traceback", stderr)


if __name__ == "__main__":
    unittest.main()
