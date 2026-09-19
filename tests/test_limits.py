"""Resource limits must fail clearly while normal corpus cases remain exact."""

import tempfile
import subprocess
import unittest
from pathlib import Path

from linediff.diff import compute_diff, count_nodes
from linediff.limits import DiffLimitError, MAX_INPUT_BYTES, MAX_LINES, MAX_LINE_CHARS
from linediff.model import Atom, ListNode
from linediff.parser import TreeSitterParser
from linediff.structural import analyze_python_changes
from test_cli_contract import run_cli


class LimitTests(unittest.TestCase):
    def test_direct_api_rejects_excessive_bytes_lines_and_line_width(self):
        for content in ('x' * (MAX_INPUT_BYTES + 1),
                        'x\n' * (MAX_LINES + 1),
                        'x' * (MAX_LINE_CHARS + 1)):
            with self.subTest(length=len(content)):
                with self.assertRaises(DiffLimitError):
                    compute_diff(content, '')

    def test_cli_rejects_large_file_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            large = Path(directory, 'large.txt')
            small = Path(directory, 'small.txt')
            large.write_bytes(b'x' * (MAX_INPUT_BYTES + 1))
            small.write_text('small\n', encoding='utf-8')
            result = run_cli(str(large), str(small))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
            self.assertIn(b'4 MiB input limit', result.stderr)
            self.assertNotIn(b'Traceback', result.stderr)

    def test_stdin_limit(self):
        result = run_cli(input_bytes=b'x' * (MAX_INPUT_BYTES * 2 + 1))
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'8 MiB pair input limit', result.stderr)

    def test_structural_budget_falls_back_without_losing_text(self):
        before = 'x = "' + 'a' * (1024 * 1024) + '"\n'
        after = before.replace('a"', 'b"')
        result = analyze_python_changes(before, after)
        self.assertFalse(result.supported)
        self.assertIn('1 MiB', result.reason)

    def test_node_count_does_not_recurse(self):
        node = Atom('x', 0)
        for _ in range(1500):
            node = ListNode([node], 0)
        self.assertEqual(count_nodes(node), 1501)

    def test_parser_rejects_oversized_direct_input(self):
        parser = TreeSitterParser()
        with self.assertRaises(ValueError):
            parser.parse_content('x' * (MAX_INPUT_BYTES + 1), language='python')

    def test_large_alignment_uses_exact_whole_file_patch(self):
        old = ''.join('old {:04d}\n'.format(index) for index in range(3000))
        new = ''.join('new {:04d}\n'.format(index) for index in range(3000))
        records = compute_diff(old, new)
        self.assertEqual(records[2], '@@ -1,3000 +1,3000 @@')
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory, 'left.txt')
            left.write_text(old, encoding='utf-8')
            patch = Path(directory, 'change.patch')
            patch.write_text('--- a/left.txt\n+++ b/left.txt\n' + '\n'.join(records[2:]) + '\n', encoding='utf-8')
            applied = subprocess.run(['git', 'apply', str(patch)], cwd=directory, capture_output=True)
            self.assertEqual(applied.returncode, 0, applied.stderr.decode(errors='replace'))
            self.assertEqual(left.read_text(encoding='utf-8'), new)


if __name__ == '__main__':
    unittest.main()
