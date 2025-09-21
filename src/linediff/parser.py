"""
Tree-sitter based syntax-aware parser for linediff.
Converts ASTs into Syntax trees (List/Atom nodes) for structural diffing.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional, Union, Any
import os
import re
from pathlib import Path

try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_json
    import tree_sitter_html
    import tree_sitter_css
    import tree_sitter_rust
    import tree_sitter_go
    import tree_sitter_java
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None

# Import from diff.py for consistency
from .diff import Atom, ListNode

@dataclass
class LanguageConfig:
    """Configuration for a programming language."""
    name: str
    extensions: List[str]
    parser_class: Any
    atom_types: Set[str]  # AST node types that should be treated as atoms
    list_types: Set[str]  # AST node types that should be treated as lists
    delimiter_types: Dict[str, str]  # Node types and their preferred delimiters

# Language configurations
LANGUAGE_CONFIGS = {
    'python': LanguageConfig(
        name='python',
        extensions=['.py', '.pyw', '.pyi'],
        parser_class=tree_sitter_python.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string', 'integer', 'float', 'identifier', 'comment'},
        list_types={'module', 'function_definition', 'class_definition', 'block', 'expression_list'},
        delimiter_types={
            'function_definition': '\n',
            'class_definition': '\n\n',
            'block': '\n',
            'expression_list': ', '
        }
    ),
    'javascript': LanguageConfig(
        name='javascript',
        extensions=['.js', '.jsx', '.ts', '.tsx', '.mjs'],
        parser_class=tree_sitter_javascript.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string', 'number', 'identifier', 'comment'},
        list_types={'program', 'function_declaration', 'class_declaration', 'block_statement', 'array'},
        delimiter_types={
            'function_declaration': '\n',
            'class_declaration': '\n\n',
            'block_statement': '\n',
            'array': ', '
        }
    ),
    'json': LanguageConfig(
        name='json',
        extensions=['.json', '.jsonc'],
        parser_class=tree_sitter_json.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string', 'number', 'true', 'false', 'null'},
        list_types={'object', 'array'},
        delimiter_types={
            'object': ', ',
            'array': ', '
        }
    ),
    'html': LanguageConfig(
        name='html',
        extensions=['.html', '.htm', '.xml'],
        parser_class=tree_sitter_html.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'text', 'comment', 'attribute_value'},
        list_types={'element', 'document', 'start_tag', 'end_tag'},
        delimiter_types={
            'element': '',
            'document': '',
            'start_tag': '',
            'end_tag': ''
        }
    ),
    'css': LanguageConfig(
        name='css',
        extensions=['.css', '.scss', '.sass', '.less'],
        parser_class=tree_sitter_css.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string', 'number', 'identifier', 'comment'},
        list_types={'stylesheet', 'rule_set', 'declaration_list', 'selectors'},
        delimiter_types={
            'rule_set': '\n',
            'declaration_list': '\n',
            'selectors': ', '
        }
    ),
    'rust': LanguageConfig(
        name='rust',
        extensions=['.rs'],
        parser_class=tree_sitter_rust.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string_literal', 'integer_literal', 'identifier', 'line_comment', 'block_comment'},
        list_types={'source_file', 'function_item', 'struct_item', 'impl_item', 'block'},
        delimiter_types={
            'function_item': '\n\n',
            'struct_item': '\n\n',
            'impl_item': '\n\n',
            'block': '\n'
        }
    ),
    'go': LanguageConfig(
        name='go',
        extensions=['.go'],
        parser_class=tree_sitter_go.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string_literal', 'int_literal', 'identifier', 'comment'},
        list_types={'source_file', 'function_declaration', 'type_declaration', 'block'},
        delimiter_types={
            'function_declaration': '\n\n',
            'type_declaration': '\n\n',
            'block': '\n'
        }
    ),
    'java': LanguageConfig(
        name='java',
        extensions=['.java'],
        parser_class=tree_sitter_java.language() if TREE_SITTER_AVAILABLE else None,
        atom_types={'string_literal', 'integer_literal', 'identifier', 'line_comment', 'block_comment'},
        list_types={'program', 'class_declaration', 'method_declaration', 'block'},
        delimiter_types={
            'class_declaration': '\n\n',
            'method_declaration': '\n\n',
            'block': '\n'
        }
    )
}

class TreeSitterParser:
    """Tree-sitter based parser for syntax-aware diffing."""

    def __init__(self):
        self.parsers: Dict[str, Any] = {}
        if TREE_SITTER_AVAILABLE:
            self._initialize_parsers()

    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        for lang_name, config in LANGUAGE_CONFIGS.items():
            if config.parser_class:
                try:
                    parser = tree_sitter.Parser()
                    parser.set_language(config.parser_class)
                    self.parsers[lang_name] = parser
                except Exception as e:
                    print(f"Warning: Failed to initialize parser for {lang_name}: {e}")

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language based on file extension."""
        if not file_path:
            return None

        path = Path(file_path)
        extension = path.suffix.lower()

        for lang_name, config in LANGUAGE_CONFIGS.items():
            if extension in config.extensions:
                return lang_name

        return None

    def parse_content(self, content: str, language: Optional[str] = None, file_path: Optional[str] = None) -> ListNode:
        """Parse content into syntax tree using tree-sitter or fallback to regex."""
        if not TREE_SITTER_AVAILABLE:
            return self._fallback_parse(content)

        # Detect language if not provided
        if not language and file_path:
            language = self.detect_language(file_path)

        if not language or language not in self.parsers:
            return self._fallback_parse(content)

        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf-8'))
            if tree is None or tree.root_node is None:
                raise ValueError("Tree-sitter returned invalid tree")
            config = LANGUAGE_CONFIGS[language]
            return self._ast_to_syntax_tree(tree.root_node, config, content)
        except UnicodeEncodeError as e:
            print(f"Warning: Encoding error during tree-sitter parsing for {language}: {e}")
            return self._fallback_parse(content)
        except Exception as e:
            print(f"Warning: Tree-sitter parsing failed for {language}: {e}")
            return self._fallback_parse(content)

    def _ast_to_syntax_tree(self, node: Any, config: LanguageConfig, content: str, position: int = 0) -> Union[ListNode, Atom]:
        """Convert AST node to Syntax tree (List/Atom)."""
        node_type = node.type

        # Get node text
        start_byte = node.start_byte
        end_byte = node.end_byte
        node_text = content[start_byte:end_byte]

        # Determine if this is an atom or list
        if node_type in config.atom_types or not node.children:
            return Atom(node_text, position)

        # This is a list node
        children = []
        child_position = position

        for child in node.children:
            child_node = self._ast_to_syntax_tree(child, config, content, child_position)
            children.append(child_node)
            child_position += 1

        return ListNode(children, position)

    def _fallback_parse(self, content: str) -> ListNode:
        """Fallback to regex-based line/word parsing."""
        lines = content.splitlines()
        atoms = [Atom(line, i) for i, line in enumerate(lines)]
        return ListNode(atoms, 0)

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(LANGUAGE_CONFIGS.keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in LANGUAGE_CONFIGS and language in self.parsers

# Global parser instance
_parser_instance = None

def get_parser() -> TreeSitterParser:
    """Get singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = TreeSitterParser()
    return _parser_instance

def parse_to_tree(content: str, file_path: Optional[str] = None) -> ListNode:
    """Parse content into syntax tree with automatic language detection."""
    parser = get_parser()
    return parser.parse_content(content, file_path=file_path)