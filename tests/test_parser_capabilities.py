"""Optional grammar availability, UTF-8 offsets, and fallback behavior."""

import os
import unittest

from linediff.diff import parse_to_tree as diff_parse_to_tree
from linediff.model import Atom, ListNode
from linediff.parser import LANGUAGE_CONFIGS, TreeSitterParser
from linediff.structural import analyze_python_changes


SAMPLES = {
    "python": "def café():\n    return '🌍'\n",
    "javascript": "function f() { return 1; }",
    "json": '{"x":1}',
    "html": "<p>ok</p>",
    "css": "p { color: red; }",
    "rust": "fn main() {}",
    "go": "package main",
    "java": "class Main {}",
}


def atoms(node):
    if isinstance(node, Atom):
        yield node
    else:
        for child in node.children:
            yield from atoms(child)


class ParserCapabilityTests(unittest.TestCase):
    def test_expected_installation_profile(self):
        parser = TreeSitterParser()
        expected = os.environ.get("LINEDIFF_EXPECT_PARSERS")
        if expected == "none":
            self.assertEqual(parser.get_supported_languages(), [])
        elif expected == "python":
            self.assertEqual(parser.get_supported_languages(), ["python"])
        elif expected == "full":
            self.assertEqual(set(parser.get_supported_languages()), set(LANGUAGE_CONFIGS))
        elif expected is not None:
            self.fail("Unknown LINEDIFF_EXPECT_PARSERS value: " + expected)

    def test_only_real_grammar_extensions_are_detected(self):
        parser = TreeSitterParser()
        self.assertEqual(parser.detect_language("file.py"), "python")
        self.assertEqual(parser.detect_language("file.json"), "json")
        for extension in (".ts", ".tsx", ".jsonc", ".xml", ".scss"):
            self.assertIsNone(parser.detect_language("file" + extension))

    def test_installed_grammars_parse_their_language(self):
        parser = TreeSitterParser()
        for language in parser.get_supported_languages():
            with self.subTest(language=language):
                tree = parser.parse_raw(SAMPLES[language], language=language)
                self.assertIsNotNone(tree)
                self.assertFalse(tree.root_node.has_error)
                self.assertIsInstance(parser.parse_content(SAMPLES[language], language=language), ListNode)

    def test_python_utf8_byte_offsets_and_backend(self):
        parser = TreeSitterParser()
        source = SAMPLES["python"]
        if not parser.is_language_supported("python"):
            self.assertEqual(analyze_python_changes(source, source).parser_backend, "python-ast")
            self.assertEqual(len(diff_parse_to_tree(source, "sample.py").children), 2)
            return

        parsed = parser.parse_content(source, language="python")
        source_bytes = source.encode("utf-8")
        leaves = list(atoms(parsed))
        self.assertIn("café", [leaf.value for leaf in leaves])
        for leaf in leaves:
            value = leaf.value.encode("utf-8")
            self.assertEqual(source_bytes[leaf.position:leaf.position + len(value)], value)
        result = analyze_python_changes(source, source.replace("🌍", "🌙"))
        self.assertEqual(result.parser_backend, "tree-sitter + python-ast")
        self.assertEqual(result.changes[0].definition, "café")
        self.assertEqual(result.changes[0].old_lines, (1, 2))

    def test_invalid_syntax_returns_line_tree(self):
        parser = TreeSitterParser()
        invalid = "def broken(:\n    pass\n"
        fallback = parser.parse_content(invalid, language="python")
        self.assertIsInstance(fallback, ListNode)
        self.assertEqual([node.value for node in fallback.children], invalid.splitlines())

    def test_line_fallback_positions_are_utf8_byte_offsets(self):
        fallback = TreeSitterParser()._fallback_parse("é\r\nx\n")
        self.assertEqual([(node.value, node.position) for node in fallback.children], [
            ("é", 0), ("x", 4)
        ])


if __name__ == "__main__":
    unittest.main()
