#!/usr/bin/env python3
"""CLI entry point for linediff."""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
from .diff import compute_diff


def detect_language(file_path: str) -> str:
    """Detect language based on file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.rs': 'rust',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
    }
    return lang_map.get(ext, 'text')


def read_file_content(file_path: str) -> str:
    """Read content from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Error: Cannot decode file '{file_path}' as UTF-8.", file=sys.stderr)
        sys.exit(1)


def read_stdin_content() -> str:
    """Read content from stdin."""
    return sys.stdin.read()


def parse_git_diff_stdin(stdin_content: str) -> Tuple[str, str, str, str]:
    """Parse Git diff format from stdin for --ext-diff."""
    # Git --ext-diff sends: old-file new-file old-hex new-hex
    # Followed by old-mode new-mode
    # Then old content, then new content
    # But for simplicity, assume stdin has two parts separated by a marker
    # Actually, for external diff, Git provides the files as args, but perhaps here we parse diff output.
    # For now, assume stdin has the diff text, but that doesn't make sense.
    # Perhaps for git diff | linediff, to reformat.
    # But the task says "parsing Git's diff format", so perhaps parse unified diff from stdin.
    # To extract old and new content.
    # This is complex. For now, assume stdin has old content, then ---, then new content or something.
    # Let's assume simple: if no files, read two contents from stdin separated by a line with ---.
    lines = stdin_content.splitlines()
    separator_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '---':
            separator_index = i
            break
    if separator_index == -1:
        print("Error: Stdin input must contain '---' separator for old and new content.", file=sys.stderr)
        sys.exit(1)
    old_content = '\n'.join(lines[:separator_index])
    new_content = '\n'.join(lines[separator_index + 1:])
    return old_content, new_content, 'old', 'new'


def format_diff(diff_lines: List[str], fromfile: str, tofile: str, lang: str = 'text', display_mode: str = 'unified') -> str:
    """Format diff lines according to the specified display mode."""
    if display_mode == 'unified':
        return format_unified_diff(diff_lines, fromfile, tofile, lang)
    elif display_mode == 'side-by-side':
        return format_side_by_side_diff(diff_lines, fromfile, tofile, lang)
    elif display_mode == 'inline':
        return format_inline_diff(diff_lines, fromfile, tofile, lang)
    else:
        raise ValueError(f"Unknown display mode: {display_mode}")

def format_unified_diff(diff_lines: List[str], fromfile: str, tofile: str, lang: str = 'text') -> str:
    """Format diff lines into unified diff style with headers."""
    # Add header
    header = f"--- {fromfile}\n+++ {tofile}\n"
    if not diff_lines:
        return header.rstrip()

    # Remove any existing headers from diff_lines
    cleaned_lines = diff_lines[:]
    if cleaned_lines and cleaned_lines[0].startswith('---'):
        cleaned_lines = cleaned_lines[2:]  # Remove --- and +++ lines

    # If diff_lines already have hunk markers (from difflib), just add header
    if any(line.startswith('@@') for line in cleaned_lines):
        return header + '\n'.join(cleaned_lines)

    # Otherwise, for structural diff, add hunk markers
    # Simple implementation: treat all as one hunk
    old_count = sum(1 for line in cleaned_lines if not line.startswith('+'))
    new_count = sum(1 for line in cleaned_lines if not line.startswith('-'))
    hunk = f"@@ -1,{old_count} +1,{new_count} @@\n" + '\n'.join(cleaned_lines)
    return header + hunk

def format_side_by_side_diff(diff_lines: List[str], fromfile: str, tofile: str, lang: str = 'text') -> str:
    """Format diff lines in side-by-side style."""
    if not diff_lines:
        return f"Files {fromfile} and {tofile} are identical"

    # If diff_lines already contain unified diff format (from difflib), parse it
    if any(line.startswith('@@') for line in diff_lines) or any(line.startswith('---') for line in diff_lines):
        return format_side_by_side_from_unified(diff_lines, fromfile, tofile)

    # Otherwise, handle structural diff lines (simple format)
    left_lines = []
    right_lines = []

    for line in diff_lines:
        if line.startswith('-'):
            left_lines.append(line[1:])
            right_lines.append('')
        elif line.startswith('+'):
            left_lines.append('')
            right_lines.append(line[1:])
        else:
            # Context line
            content = line[1:] if line.startswith(' ') else line
            left_lines.append(content)
            right_lines.append(content)

    return format_side_by_side_lines(left_lines, right_lines, fromfile, tofile)

def format_side_by_side_from_unified(diff_lines: List[str], fromfile: str, tofile: str) -> str:
    """Parse unified diff and format as side-by-side."""
    left_lines = []
    right_lines = []

    for line in diff_lines:
        if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
            # Headers - skip for side-by-side
            continue
        elif line.startswith(' '):
            # Context line
            content = line[1:]
            left_lines.append(content)
            right_lines.append(content)
        elif line.startswith('-'):
            # Deletion
            content = line[1:]
            left_lines.append(content)
            right_lines.append('')
        elif line.startswith('+'):
            # Addition
            content = line[1:]
            left_lines.append('')
            right_lines.append(content)

    return format_side_by_side_lines(left_lines, right_lines, fromfile, tofile)

def format_side_by_side_lines(left_lines: List[str], right_lines: List[str], fromfile: str, tofile: str) -> str:
    """Format two lists of lines in side-by-side format."""
    max_left_width = max(len(line) for line in left_lines) if left_lines else 0
    max_right_width = max(len(line) for line in right_lines) if right_lines else 0
    left_width = max(max_left_width + 2, 30)
    right_width = max(max_right_width + 2, 30)

    result = f"--- {fromfile} +++ {tofile}\n"
    separator = " │ "

    for left, right in zip(left_lines, right_lines):
        left_display = left.ljust(left_width)
        right_display = right.ljust(right_width)
        if left and not right:
            result += f"\033[31m{left_display}\033[0m{separator}{right_display}\n"  # Red for deletions
        elif right and not left:
            result += f"{left_display}{separator}\033[32m{right_display}\033[0m\n"  # Green for additions
        else:
            result += f"{left_display}{separator}{right_display}\n"

    return result

def format_inline_diff(diff_lines: List[str], fromfile: str, tofile: str, lang: str = 'text') -> str:
    """Format diff lines with inline changes highlighted."""
    if not diff_lines:
        return f"Files {fromfile} and {tofile} are identical"

    result = f"--- {fromfile}\n+++ {tofile}\n"

    for line in diff_lines:
        if line.startswith('-'):
            result += f"\033[31m{line}\033[0m\n"  # Red for deletions
        elif line.startswith('+'):
            result += f"\033[32m{line}\033[0m\n"  # Green for additions
        else:
            result += f"{line}\n"

    return result


def main():
    parser = argparse.ArgumentParser(description="A lightweight line diff tool with Git integration.")
    parser.add_argument("files", nargs='*', help="Files to compare or Git external diff args")
    parser.add_argument("--check-only", action="store_true", help="Check if files are identical (exit code 0 if same, 1 if different)")
    parser.add_argument("--language", help="Override language detection")
    parser.add_argument("--display", choices=['unified', 'side-by-side', 'inline'], default='unified',
                       help="Display mode for diffs (default: unified)")
    args = parser.parse_args()

    # Handle different input modes
    if len(args.files) == 7:
        # Git external diff: path old-file old-hex old-mode new-file new-hex new-mode
        _, old_file, _, _, new_file, _, _ = args.files
        content1 = read_file_content(old_file)
        content2 = read_file_content(new_file)
        fromfile = old_file
        tofile = new_file
    elif len(args.files) == 2:
        # Two files
        file1, file2 = args.files
        content1 = read_file_content(file1)
        content2 = read_file_content(file2)
        fromfile = file1
        tofile = file2
    elif len(args.files) == 0:
        # Read from stdin
        stdin_content = read_stdin_content()
        content1, content2, fromfile, tofile = parse_git_diff_stdin(stdin_content)
    else:
        print("Error: Provide 0 files (stdin), 2 files, or 7 files (Git external diff).", file=sys.stderr)
        sys.exit(1)

    # Detect language
    lang = args.language or detect_language(fromfile)

    # Compute diff
    try:
        diff_lines = compute_diff(content1, content2, fromfile, tofile)
    except Exception as e:
        print(f"Error: Failed to compute diff: {e}", file=sys.stderr)
        sys.exit(1)

    if args.check_only:
        # Check if identical
        if not diff_lines:
            sys.exit(0)  # identical
        else:
            sys.exit(1)  # different
    else:
        # Output formatted diff
        try:
            formatted_diff = format_diff(diff_lines, fromfile, tofile, lang, args.display)
            print(formatted_diff)
        except Exception as e:
            print(f"Error: Failed to format diff: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()