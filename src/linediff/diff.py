"""Exact line diffs and sequence alignment shared with structural analysis."""

import difflib
from typing import List, Optional, Tuple, Union

from .model import Atom, ListNode
from .parser import TREE_SITTER_AVAILABLE, parse_to_tree as parser_parse_to_tree
from .limits import validate_text


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
                    scores[old_index][new_index] = (
                        scores[old_index - 1][new_index - 1] + 1
                    )
                else:
                    scores[old_index][new_index] = max(
                        scores[old_index - 1][new_index],
                        scores[old_index][new_index - 1],
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
        if len(left_lines) * len(right_lines) > 8_000_000:
            return self._whole_file_diff(left_lines, right_lines)
        records = []
        for index, record in enumerate(
            difflib.unified_diff(left_lines, right_lines, lineterm="\n")
        ):
            if record.endswith("\n"):
                records.append(record[:-1])
            else:
                records.append(record)
                if index >= 2 and record[:1] in (" ", "+", "-"):
                    records.append("\\ No newline at end of file")
        return records

    def _whole_file_diff(
        self, left_lines: List[str], right_lines: List[str]
    ) -> List[str]:
        """Emit an exact patch with broad context when fine alignment is too costly."""
        old_start = 1 if left_lines else 0
        new_start = 1 if right_lines else 0
        records = [
            "--- ",
            "+++ ",
            "@@ -{},{} +{},{} @@".format(
                old_start, len(left_lines), new_start, len(right_lines)
            ),
        ]
        for prefix, lines in (("-", left_lines), ("+", right_lines)):
            for line in lines:
                if line.endswith("\n"):
                    records.append(prefix + line[:-1])
                else:
                    records.append(prefix + line)
                    records.append("\\ No newline at end of file")
        return records


def count_nodes(node: Union[ListNode, Atom]) -> int:
    """Count syntax nodes in a tree returned by the parser API."""
    count = 0
    pending = [node]
    while pending:
        current = pending.pop()
        count += 1
        if isinstance(current, ListNode):
            pending.extend(current.children)
    return count


def parse_to_tree(content: str, file_path: Optional[str] = None) -> ListNode:
    """Compatibility wrapper for the optional parser API."""
    return parser_parse_to_tree(content, file_path)


def compute_diff(
    left_content: str,
    right_content: str,
    left_file_path: Optional[str] = None,
    right_file_path: Optional[str] = None,
) -> List[str]:
    """Return exact unified records; structural annotations are separate."""
    validate_text(left_content, "Left input")
    validate_text(right_content, "Right input")
    if left_content == right_content:
        return []
    return DiffEngine().fallback_diff(
        left_content.splitlines(keepends=True),
        right_content.splitlines(keepends=True),
    )
