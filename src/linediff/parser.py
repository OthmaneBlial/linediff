"""Optional Tree-sitter parsing with independent grammar loading.

Only an installed and successfully initialized grammar counts as available.
The CLI's Python definition view can also work without this optional extra by
using Python's built-in ``ast`` module.
"""

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .model import Atom, ListNode
from .limits import MAX_INPUT_BYTES


@dataclass(frozen=True)
class LanguageConfig:
    name: str
    module: str
    extensions: Tuple[str, ...]
    atom_types: Tuple[str, ...]


LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        "python", "tree_sitter_python", (".py", ".pyw", ".pyi"),
        ("string", "integer", "float", "identifier", "comment"),
    ),
    "javascript": LanguageConfig(
        "javascript", "tree_sitter_javascript", (".js", ".jsx", ".mjs", ".cjs"),
        ("string", "number", "identifier", "comment"),
    ),
    "json": LanguageConfig(
        "json", "tree_sitter_json", (".json",),
        ("string", "number", "true", "false", "null"),
    ),
    "html": LanguageConfig(
        "html", "tree_sitter_html", (".html", ".htm"),
        ("text", "comment", "attribute_value"),
    ),
    "css": LanguageConfig(
        "css", "tree_sitter_css", (".css",),
        ("string_value", "integer_value", "identifier", "comment"),
    ),
    "rust": LanguageConfig(
        "rust", "tree_sitter_rust", (".rs",),
        ("string_literal", "integer_literal", "identifier", "line_comment", "block_comment"),
    ),
    "go": LanguageConfig(
        "go", "tree_sitter_go", (".go",),
        ("interpreted_string_literal", "int_literal", "identifier", "comment"),
    ),
    "java": LanguageConfig(
        "java", "tree_sitter_java", (".java",),
        ("string_literal", "decimal_integer_literal", "identifier", "line_comment", "block_comment"),
    ),
}

TREE_SITTER_AVAILABLE = importlib.util.find_spec("tree_sitter") is not None


class TreeSitterParser:
    """Load installed grammars on demand and preserve UTF-8 byte positions."""

    def __init__(self) -> None:
        self.parsers: Dict[str, Any] = {}
        self.unavailable: Dict[str, str] = {}

    def _get_parser(self, language: str) -> Optional[Any]:
        if language in self.parsers:
            return self.parsers[language]
        if language in self.unavailable:
            return None
        config = LANGUAGE_CONFIGS.get(language)
        if config is None:
            return None
        try:
            from tree_sitter import Language, Parser

            grammar = importlib.import_module(config.module)
            parser = Parser(Language(grammar.language()))
        except (ImportError, AttributeError, TypeError, ValueError) as error:
            self.unavailable[language] = str(error)
            return None
        self.parsers[language] = parser
        return parser

    def detect_language(self, file_path: Optional[str]) -> Optional[str]:
        if not file_path:
            return None
        extension = Path(file_path).suffix.lower()
        for language, config in LANGUAGE_CONFIGS.items():
            if extension in config.extensions:
                return language
        return None

    def parse_raw(self, content: str, language: Optional[str] = None,
                  file_path: Optional[str] = None) -> Optional[Any]:
        if len(content.encode('utf-8')) > MAX_INPUT_BYTES:
            return None
        selected = language or self.detect_language(file_path)
        if not selected:
            return None
        parser = self._get_parser(selected)
        if parser is None:
            return None
        try:
            return parser.parse(content.encode("utf-8"))
        except (UnicodeEncodeError, ValueError, RuntimeError):
            return None

    def parse_content(self, content: str, language: Optional[str] = None,
                      file_path: Optional[str] = None) -> ListNode:
        """Return a syntax tree or an explicit line-based fallback tree."""
        if len(content.encode('utf-8')) > MAX_INPUT_BYTES:
            raise ValueError('Parser input exceeds the 4 MiB limit')
        tree = self.parse_raw(content, language=language, file_path=file_path)
        if tree is None or tree.root_node.has_error:
            return self._fallback_parse(content)
        source_bytes = content.encode("utf-8")
        try:
            root = self._ast_to_syntax_tree(tree.root_node, source_bytes, LANGUAGE_CONFIGS[language or self.detect_language(file_path)])
        except RecursionError:
            return self._fallback_parse(content)
        if isinstance(root, Atom):
            return ListNode([root], 0)
        return root

    def _ast_to_syntax_tree(self, node: Any, source_bytes: bytes,
                            config: LanguageConfig) -> Union[ListNode, Atom]:
        """Use byte offsets from Tree-sitter against UTF-8 bytes, not Python characters."""
        if node.type in config.atom_types or not node.children:
            value = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
            return Atom(value, node.start_byte)
        children = [self._ast_to_syntax_tree(child, source_bytes, config) for child in node.children]
        return ListNode(children, node.start_byte)

    def _fallback_parse(self, content: str) -> ListNode:
        atoms = []
        offset = 0
        for line in content.splitlines(keepends=True):
            if line.endswith('\r\n'):
                value = line[:-2]
            elif line.endswith(('\n', '\r')):
                value = line[:-1]
            else:
                value = line
            atoms.append(Atom(value, offset))
            offset += len(line.encode('utf-8'))
        return ListNode(atoms, 0)

    def get_supported_languages(self) -> List[str]:
        """Return languages with usable installed grammars, not all registry entries."""
        return [language for language in LANGUAGE_CONFIGS if self.is_language_supported(language)]

    def is_language_supported(self, language: str) -> bool:
        return self._get_parser(language) is not None


_parser_instance: Optional[TreeSitterParser] = None


def get_parser() -> TreeSitterParser:
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TreeSitterParser()
    return _parser_instance


def parse_to_tree(content: str, file_path: Optional[str] = None) -> ListNode:
    return get_parser().parse_content(content, file_path=file_path)
