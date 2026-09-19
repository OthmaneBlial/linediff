"""Exact line diffs and sequence alignment shared with structural analysis."""

import difflib
from typing import List, Optional, Tuple, Union

from .model import Atom, ListNode
from .parser import TREE_SITTER_AVAILABLE, parse_to_tree as parser_parse_to_tree


TREE_SITTER_PARSER_AVAILABLE = TREE_SITTER_AVAILABLE


class DiffEngine:
    """Small utilities for exact text records and ordered definition anchors."""

    def lcs_linear(self, left: List[str], right: List[str]) -> List[Tuple[int, int]]:
        """Return index pairs in a longest common subsequence."""
        rows, columns = len(left), len(right)
        scores = [[0] * (columns + 1) for _ in range(rows + 1)]
        for old_index in range(1, rows + 1):
            for new_index in range(1, columns + 1):
                if left[old_index - 1] == right[new_index - 1]:
                    scores[old_index][new_index] = scores[old_index - 1][new_index - 1] + 1
                else:
                    scores[old_index][new_index] = max(
                        scores[old_index - 1][new_index], scores[old_index][new_index - 1]
                    )
        matches = []
        old_index, new_index = rows, columns
        while old_index and new_index:
            if left[old_index - 1] == right[new_index - 1]:
                matches.append((old_index - 1, new_index - 1))
                old_index -= 1
                new_index -= 1
            elif scores[old_index - 1][new_index] > scores[old_index][new_index - 1]:
                old_index -= 1
            else:
                new_index -= 1
        matches.reverse()
        return matches

    def fallback_diff(self, left_lines: List[str], right_lines: List[str]) -> List[str]:
        """Return unified records while preserving exact source line endings."""
        records = []
        for index, record in enumerate(
            difflib.unified_diff(left_lines, right_lines, lineterm='\n')
        ):
            if record.endswith('\n'):
                records.append(record[:-1])
            else:
                records.append(record)
                if index >= 2 and record[:1] in (' ', '+', '-'):
                    records.append('\\ No newline at end of file')
        return records


def count_nodes(node: Union[ListNode, Atom]) -> int:
    """Count syntax nodes in a tree returned by the parser API."""
    if isinstance(node, Atom):
        return 1
    return 1 + sum(count_nodes(child) for child in node.children)


def parse_to_tree(content: str, file_path: Optional[str] = None) -> ListNode:
    """Compatibility wrapper for the optional parser API."""
    return parser_parse_to_tree(content, file_path)


def compute_diff(left_content: str, right_content: str,
                 left_file_path: Optional[str] = None,
                 right_file_path: Optional[str] = None) -> List[str]:
    """Return exact unified records; structural annotations are separate."""
    if left_content == right_content:
        return []
    return DiffEngine().fallback_diff(
        left_content.splitlines(keepends=True),
        right_content.splitlines(keepends=True),
    )
