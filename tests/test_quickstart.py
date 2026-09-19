"""Keep the shown quickstart output tied to the actual CLI."""

import unittest
from test_cli_contract import ROOT, run_cli


class QuickstartTests(unittest.TestCase):
    def test_structural_example_matches_documented_output(self):
        document = (ROOT / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")
        expected = document.split("```text\n", 1)[1].split("\n```", 1)[0] + "\n"
        result = run_cli(
            "--display",
            "structural",
            "tests/fixtures/moved_function.old.py",
            "tests/fixtures/moved_function.new.py",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode("utf-8").replace("\r\n", "\n"), expected)


if __name__ == "__main__":
    unittest.main()
