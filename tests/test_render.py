"""Human-readable views must remain legible and safe in pipes."""

import unittest

from linediff.diff import compute_diff
from linediff.render import _cell_width, format_side_by_side_diff
from test_cli_contract import run_cli


class RenderTests(unittest.TestCase):
    def test_side_by_side_width_and_line_numbers(self):
        left = "head\n" + "x" * 120 + "\n"
        right = "head\n" + "y" * 120 + "\n"
        records = compute_diff(left, right)
        for width in (80, 120):
            with self.subTest(width=width):
                output = format_side_by_side_diff(records, "old", "new", width=width)
                self.assertTrue(all(len(line) <= width for line in output.splitlines()))
                self.assertIn("    2-", output)
                self.assertIn("    2+", output)
                self.assertIn("…", output)

    def test_redirected_output_has_no_ansi_and_always_can_force_it(self):
        old = "tests/fixtures/replace.old.txt"
        new = "tests/fixtures/replace.new.txt"
        for mode in ("inline", "side-by-side"):
            with self.subTest(mode=mode):
                auto = run_cli("--display", mode, old, new)
                self.assertEqual(auto.returncode, 0)
                self.assertNotIn(b"\x1b[", auto.stdout)
                forced = run_cli("--color", "always", "--display", mode, old, new)
                self.assertIn(b"\x1b[", forced.stdout)
                never = run_cli("--color", "never", "--display", mode, old, new)
                self.assertNotIn(b"\x1b[", never.stdout)

    def test_side_by_side_marks_final_newline(self):
        output = format_side_by_side_diff(
            compute_diff("old", "new\n"), "old", "new", width=80
        )
        self.assertIn("No final newline", output)

    def test_input_escape_is_printed_as_text(self):
        output = format_side_by_side_diff(
            compute_diff("a\x1b[2J\n", "b\n"), "old", "new", width=80
        )
        self.assertNotIn("\x1b", output)
        self.assertIn("\\u001b", output)

    def test_wide_unicode_respects_terminal_cells(self):
        output = format_side_by_side_diff(
            compute_diff("界" * 40 + "\n", "語" * 40 + "\n"), "old", "new", width=80
        )
        self.assertTrue(all(_cell_width(line) <= 80 for line in output.splitlines()))


if __name__ == "__main__":
    unittest.main()
