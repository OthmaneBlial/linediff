"""Oracles for Python definition matching and the opt-in structural view."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from linediff.structural import analyze_python_changes


ROOT = Path(__file__).resolve().parent.parent


def fixture(case_id, side):
    return (ROOT / "tests" / "fixtures" / (case_id + "." + side + ".py")).read_text(encoding="utf-8")


def cli(*arguments):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "linediff"] + list(arguments),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class StructuralTests(unittest.TestCase):
    def test_moved_function_has_provenance(self):
        result = analyze_python_changes(fixture("moved_function", "old"), fixture("moved_function", "new"))
        self.assertTrue(result.supported)
        self.assertEqual(len(result.changes), 1)
        change = result.changes[0]
        self.assertEqual((change.kind, change.definition), ("moved", "calculate_total"))
        self.assertEqual(change.old_lines, (1, 2))
        self.assertEqual(change.new_lines, (4, 5))

    def test_signature_and_body_are_grouped(self):
        result = analyze_python_changes(fixture("signature_body", "old"), fixture("signature_body", "new"))
        self.assertEqual([(c.kind, c.definition, c.details) for c in result.changes], [
            ("changed", "calculate_total", ("signature", "body"))
        ])

    def test_class_method_is_named_without_duplicate_class_change(self):
        result = analyze_python_changes(fixture("class_method", "old"), fixture("class_method", "new"))
        self.assertEqual([(c.kind, c.definition) for c in result.changes], [("changed", "Calculator.add")])

    def test_formatting_only_does_not_invent_syntax_change(self):
        result = analyze_python_changes(fixture("format_only", "old"), fixture("format_only", "new"))
        self.assertTrue(result.supported)
        self.assertEqual(result.changes, ())

    def test_insertion_does_not_make_existing_definitions_look_moved(self):
        before = "def first():\n    pass\n\ndef second():\n    pass\n"
        after = "def added():\n    pass\n\n" + before
        result = analyze_python_changes(before, after)
        self.assertEqual([(c.kind, c.definition) for c in result.changes], [("added", "added")])

    def test_invalid_or_ambiguous_python_falls_back(self):
        invalid = analyze_python_changes("def broken(:\n", "def valid():\n    pass\n")
        self.assertFalse(invalid.supported)
        self.assertIn("parsing failed", invalid.reason)
        duplicate = analyze_python_changes("def same(): pass\ndef same(): pass\n", "def same(): pass\n")
        self.assertFalse(duplicate.supported)
        self.assertIn("ambiguous", duplicate.reason)

    def test_structural_analysis_does_not_depend_on_line_diff(self):
        with patch("difflib.unified_diff", side_effect=AssertionError("line diff unavailable")):
            result = analyze_python_changes(fixture("moved_function", "old"), fixture("moved_function", "new"))
        self.assertEqual(result.changes[0].kind, "moved")

    def test_cli_keeps_exact_text_diff_below_structural_summary(self):
        for case_id in ("moved_function", "signature_body", "class_method"):
            with self.subTest(case=case_id):
                old = "tests/fixtures/{}.old.py".format(case_id)
                new = "tests/fixtures/{}.new.py".format(case_id)
                exact = cli(old, new)
                structural = cli("--display", "structural", old, new)
                self.assertEqual((exact.returncode, structural.returncode), (0, 0))
                self.assertIn("not an applicable patch", structural.stdout)
                self.assertIn(exact.stdout.strip(), structural.stdout)
        self.assertIn("CHANGED calculate_total (signature, body)", cli(
            "--display", "structural", "tests/fixtures/signature_body.old.py",
            "tests/fixtures/signature_body.new.py"
        ).stdout)

    def test_language_override_selects_python_view_for_text_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory, "old.txt")
            new = Path(directory, "new.txt")
            old.write_text(fixture("signature_body", "old"), encoding="utf-8")
            new.write_text(fixture("signature_body", "new"), encoding="utf-8")
            fallback = cli("--display", "structural", str(old), str(new))
            forced = cli("--display", "structural", "--language", "python", str(old), str(new))
            self.assertIn("Text fallback", fallback.stdout)
            self.assertIn("CHANGED calculate_total", forced.stdout)


if __name__ == "__main__":
    unittest.main()
