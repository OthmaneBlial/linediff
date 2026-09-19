"""Terminal renderers; only the unified view is an applicable text patch."""

import re
import unicodedata
from typing import List, Optional

from .structural import StructuralResult, analyze_python_changes


HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def format_diff(
    diff_lines: List[str],
    fromfile: str,
    tofile: str,
    lang: str = "text",
    display_mode: str = "unified",
    color: bool = False,
    width: int = 100,
) -> str:
    if display_mode == "unified":
        return format_unified_diff(diff_lines, fromfile, tofile, lang)
    if display_mode == "side-by-side":
        return format_side_by_side_diff(
            diff_lines, fromfile, tofile, lang, color, width
        )
    if display_mode == "inline":
        return format_inline_diff(diff_lines, fromfile, tofile, lang, color)
    raise ValueError("Unknown display mode: {}".format(display_mode))


def format_unified_diff(
    diff_lines: List[str], fromfile: str, tofile: str, lang: str = "text"
) -> str:
    """Add user-facing filenames to already valid unified records."""
    header = "--- {}\n+++ {}\n".format(fromfile, tofile)
    if not diff_lines:
        return header.rstrip()
    if (
        len(diff_lines) < 3
        or not diff_lines[0].startswith("--- ")
        or not diff_lines[1].startswith("+++ ")
    ):
        raise ValueError("Expected unified diff records with file headers")
    return header + "\n".join(diff_lines[2:])


def _paint(value: str, tone: str, color: bool) -> str:
    return "\033[{}m{}\033[0m".format(tone, value) if color else value


def _visible(value: str) -> str:
    """Prevent source control bytes from controlling the terminal."""
    return "".join(
        char
        if char == "\t" or unicodedata.category(char) not in ("Cc", "Cf")
        else "\\u{:04x}".format(ord(char))
        for char in value
    ).expandtabs(4)


def _cell_width(value: str) -> int:
    return sum(
        0
        if unicodedata.combining(char)
        else 2
        if unicodedata.east_asian_width(char) in ("W", "F")
        else 1
        for char in value
    )


def _crop(value: str, width: int) -> str:
    value = _visible(value)
    if _cell_width(value) <= width:
        return value
    result = []
    used = 0
    for char in value:
        cell = _cell_width(char)
        if used + cell > width - 1:
            break
        result.append(char)
        used += cell
    return "".join(result) + "…"


def _rows(records: List[str]):
    """Pair adjacent removals/additions and retain hunk line numbers."""
    old_number = new_number = 0
    removals = []
    additions = []
    rows = []
    last_side = None

    def flush():
        for index in range(max(len(removals), len(additions))):
            old = removals[index] if index < len(removals) else (None, "")
            new = additions[index] if index < len(additions) else (None, "")
            rows.append(
                (
                    old[0],
                    new[0],
                    old[1],
                    new[1],
                    "-" if old[0] is not None else "",
                    "+" if new[0] is not None else "",
                )
            )
        removals.clear()
        additions.clear()

    for record in records[2:]:
        match = HUNK.match(record)
        if match:
            flush()
            old_number, new_number = map(int, match.groups())
            last_side = None
        elif record.startswith("\\ No newline"):
            flush()
            rows.append(
                (
                    None,
                    None,
                    "No final newline" if last_side == "-" else "",
                    "No final newline" if last_side == "+" else "",
                    "!",
                    "!",
                )
            )
        elif record.startswith("-"):
            removals.append((old_number, record[1:]))
            old_number += 1
            last_side = "-"
        elif record.startswith("+"):
            additions.append((new_number, record[1:]))
            new_number += 1
            last_side = "+"
        elif record.startswith(" "):
            flush()
            rows.append((old_number, new_number, record[1:], record[1:], " ", " "))
            old_number += 1
            new_number += 1
            last_side = None
    flush()
    return rows


def _summary(records: List[str]) -> str:
    additions = sum(record.startswith("+") for record in records[2:])
    removals = sum(record.startswith("-") for record in records[2:])
    hunks = sum(record.startswith("@@") for record in records[2:])
    return "+{} / -{} lines · {} hunk{}".format(
        additions, removals, hunks, "" if hunks == 1 else "s"
    )


def format_side_by_side_diff(
    diff_lines: List[str],
    fromfile: str,
    tofile: str,
    lang: str = "text",
    color: bool = False,
    width: int = 100,
) -> str:
    if not diff_lines:
        return "Files {} and {} are identical".format(fromfile, tofile)
    width = max(40, width)
    content_width = (width - 17) // 2
    rendered = [_crop("{} → {}".format(fromfile, tofile), width), _summary(diff_lines)]
    for old_no, new_no, left, right, old_mark, new_mark in _rows(diff_lines):
        left_text = _crop(left, content_width)
        left_cell = "{}{} {}{}".format(
            str(old_no).rjust(5) if old_no is not None else " " * 5,
            old_mark,
            left_text,
            " " * (content_width - _cell_width(left_text)),
        )
        right_cell = "{}{} {}".format(
            str(new_no).rjust(5) if new_no is not None else " " * 5,
            new_mark,
            _crop(right, content_width),
        )
        if old_mark == "-":
            left_cell = _paint(left_cell, "31", color)
        if new_mark == "+":
            right_cell = _paint(right_cell, "32", color)
        rendered.append(left_cell + " │ " + right_cell)
    return "\n".join(rendered)


def format_inline_diff(
    diff_lines: List[str],
    fromfile: str,
    tofile: str,
    lang: str = "text",
    color: bool = False,
) -> str:
    if not diff_lines:
        return "Files {} and {} are identical".format(fromfile, tofile)
    rendered = [
        "{} → {} (human-readable)".format(_visible(fromfile), _visible(tofile)),
        _summary(diff_lines),
    ]
    for record in diff_lines[2:]:
        safe = _visible(record)
        if record.startswith("-"):
            safe = _paint(safe, "31", color)
        elif record.startswith("+"):
            safe = _paint(safe, "32", color)
        rendered.append(safe)
    return "\n".join(rendered)


def format_structural_diff(
    diff_lines: List[str],
    fromfile: str,
    tofile: str,
    language: str,
    before: str,
    after: str,
    analysis: Optional[StructuralResult] = None,
) -> str:
    lines = ["Structural view (human-readable; not an applicable patch)"]
    if language != "python":
        lines.append(
            "Text fallback: no verified structural view for '{}'".format(language)
        )
    else:
        result = (
            analysis if analysis is not None else analyze_python_changes(before, after)
        )
        if not result.supported:
            lines.append("Text fallback: {}".format(result.reason))
        elif not result.changes:
            lines.append(
                "No indexed Python definition changed; see the text diff below."
            )
        else:
            for change in result.changes:
                old_range = (
                    "{}-{}".format(*change.old_lines) if change.old_lines else "none"
                )
                new_range = (
                    "{}-{}".format(*change.new_lines) if change.new_lines else "none"
                )
                details = (
                    " ({})".format(", ".join(change.details)) if change.details else ""
                )
                lines.append(
                    "{} {}{} [old lines {}; new lines {}]".format(
                        change.kind.upper(),
                        change.definition,
                        details,
                        old_range,
                        new_range,
                    )
                )
    lines.extend(
        ["", "Exact text diff:", format_unified_diff(diff_lines, fromfile, tofile)]
    )
    return "\n".join(lines)
