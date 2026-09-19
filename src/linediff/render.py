"""Terminal renderers; only the unified view is an applicable text patch."""

from typing import List, Optional

from .structural import StructuralResult, analyze_python_changes


def format_diff(diff_lines: List[str], fromfile: str, tofile: str,
                lang: str = 'text', display_mode: str = 'unified') -> str:
    if display_mode == 'unified':
        return format_unified_diff(diff_lines, fromfile, tofile, lang)
    if display_mode == 'side-by-side':
        return format_side_by_side_diff(diff_lines, fromfile, tofile, lang)
    if display_mode == 'inline':
        return format_inline_diff(diff_lines, fromfile, tofile, lang)
    raise ValueError("Unknown display mode: {}".format(display_mode))


def format_unified_diff(diff_lines: List[str], fromfile: str, tofile: str,
                        lang: str = 'text') -> str:
    """Add user-facing filenames to already valid unified records."""
    header = "--- {}\n+++ {}\n".format(fromfile, tofile)
    if not diff_lines:
        return header.rstrip()
    if len(diff_lines) < 3 or not diff_lines[0].startswith('--- ') or not diff_lines[1].startswith('+++ '):
        raise ValueError("Expected unified diff records with file headers")
    return header + '\n'.join(diff_lines[2:])


def format_side_by_side_diff(diff_lines: List[str], fromfile: str, tofile: str,
                             lang: str = 'text') -> str:
    if not diff_lines:
        return "Files {} and {} are identical".format(fromfile, tofile)
    left_lines = []
    right_lines = []
    for line in diff_lines[2:]:
        if line.startswith('@@') or line.startswith('\\ No newline'):
            continue
        if line.startswith(' '):
            left_lines.append(line[1:])
            right_lines.append(line[1:])
        elif line.startswith('-'):
            left_lines.append(line[1:])
            right_lines.append('')
        elif line.startswith('+'):
            left_lines.append('')
            right_lines.append(line[1:])
    return format_side_by_side_lines(left_lines, right_lines, fromfile, tofile)


def format_side_by_side_lines(left_lines: List[str], right_lines: List[str],
                              fromfile: str, tofile: str) -> str:
    left_width = max((len(line) for line in left_lines), default=0) + 2
    right_width = max((len(line) for line in right_lines), default=0) + 2
    left_width = max(left_width, 30)
    right_width = max(right_width, 30)
    result = "--- {} +++ {}\n".format(fromfile, tofile)
    separator = " │ "
    for left, right in zip(left_lines, right_lines):
        left_display = left.ljust(left_width)
        right_display = right.ljust(right_width)
        if left and not right:
            result += "\033[31m{}\033[0m{}{}\n".format(left_display, separator, right_display)
        elif right and not left:
            result += "{}{}\033[32m{}\033[0m\n".format(left_display, separator, right_display)
        else:
            result += "{}{}{}\n".format(left_display, separator, right_display)
    return result


def format_inline_diff(diff_lines: List[str], fromfile: str, tofile: str,
                       lang: str = 'text') -> str:
    if not diff_lines:
        return "Files {} and {} are identical".format(fromfile, tofile)
    result = "--- {}\n+++ {}\n".format(fromfile, tofile)
    for line in diff_lines[2:]:
        if line.startswith('-'):
            result += "\033[31m{}\033[0m\n".format(line)
        elif line.startswith('+'):
            result += "\033[32m{}\033[0m\n".format(line)
        else:
            result += line + '\n'
    return result


def format_structural_diff(diff_lines: List[str], fromfile: str, tofile: str,
                           language: str, before: str, after: str,
                           analysis: Optional[StructuralResult] = None) -> str:
    lines = ["Structural view (human-readable; not an applicable patch)"]
    if language != 'python':
        lines.append("Text fallback: no verified structural view for '{}'".format(language))
    else:
        result = analysis if analysis is not None else analyze_python_changes(before, after)
        if not result.supported:
            lines.append("Text fallback: {}".format(result.reason))
        elif not result.changes:
            lines.append("No indexed Python definition changed; see the text diff below.")
        else:
            for change in result.changes:
                old_range = '{}-{}'.format(*change.old_lines) if change.old_lines else 'none'
                new_range = '{}-{}'.format(*change.new_lines) if change.new_lines else 'none'
                details = ' ({})'.format(', '.join(change.details)) if change.details else ''
                lines.append(
                    '{} {}{} [old lines {}; new lines {}]'.format(
                        change.kind.upper(), change.definition, details, old_range, new_range
                    )
                )
    lines.extend(["", "Exact text diff:", format_unified_diff(diff_lines, fromfile, tofile)])
    return '\n'.join(lines)
