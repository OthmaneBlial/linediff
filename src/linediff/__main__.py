#!/usr/bin/env python3
"""CLI entry point for linediff."""

import argparse
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from .diff import compute_diff


class LinediffInputError(Exception):
    """A user-supplied input cannot be compared as UTF-8 text."""


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
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            content = f.read()
    except UnicodeDecodeError as error:
        raise LinediffInputError("Cannot decode '{}' as UTF-8".format(file_path)) from error
    except OSError as error:
        raise LinediffInputError("Cannot read '{}': {}".format(file_path, error.strerror or error)) from error
    if '\x00' in content:
        raise LinediffInputError("Binary file '{}' contains NUL bytes".format(file_path))
    return content


def read_git_bytes(file_path: str) -> bytes:
    """Read one Git external-diff operand, including Git's null-file sentinel."""
    if file_path == '/dev/null':
        return b''
    try:
        return Path(file_path).read_bytes()
    except OSError as error:
        raise LinediffInputError("Cannot read Git operand '{}': {}".format(file_path, error.strerror or error)) from error


def read_stdin_content() -> str:
    """Read content from stdin."""
    try:
        content = sys.stdin.buffer.read().decode('utf-8')
    except UnicodeDecodeError as error:
        raise LinediffInputError("Cannot decode stdin as UTF-8") from error
    except OSError as error:
        raise LinediffInputError("Cannot read stdin: {}".format(error)) from error
    if '\x00' in content:
        raise LinediffInputError("Binary stdin contains NUL bytes")
    return content


def parse_pair_stdin(stdin_content: str) -> Tuple[str, str, str, str]:
    """Split the legacy Linediff pair format without altering line endings."""
    separator = re.search(r'(?m)^---(?:\r?\n|$)', stdin_content)
    if separator is None:
        raise LinediffInputError("Stdin must contain a line with only '---' between the two texts")
    return stdin_content[:separator.start()], stdin_content[separator.end():], 'old', 'new'


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


def main() -> int:
    parser = argparse.ArgumentParser(description="A lightweight line diff tool with Git integration.")
    parser.add_argument("files", nargs='*', help="Two files or Git external diff arguments")
    parser.add_argument("--check-only", action="store_true", help="Check if files are identical (0 same, 1 different, 2 error)")
    parser.add_argument("--language", help="Override language detection")
    parser.add_argument("--display", choices=['unified', 'side-by-side', 'inline'], default='unified',
                       help="Display mode for diffs (default: unified)")
    args = parser.parse_args()

    git_mode = len(args.files) in (7, 9)
    modes_differ = False
    names_differ = False
    binary_git_diff = False
    try:
        if git_mode:
            # Git adds new-path and metadata for renames/copies (nine arguments).
            git_path, old_file, _, old_mode, new_file, _, new_mode = args.files[:7]
            new_path = git_path
            if len(args.files) == 9:
                new_path = args.files[7]
            names_differ = git_path != new_path
            fromfile = '/dev/null' if old_mode == '.' else 'a/' + git_path
            tofile = '/dev/null' if new_mode == '.' else 'b/' + new_path
            old_bytes = read_git_bytes(old_file)
            new_bytes = read_git_bytes(new_file)
            modes_differ = old_mode != new_mode
            try:
                content1 = old_bytes.decode('utf-8')
                content2 = new_bytes.decode('utf-8')
            except UnicodeDecodeError:
                binary_git_diff = True
            else:
                binary_git_diff = '\x00' in content1 or '\x00' in content2
            if binary_git_diff:
                if args.check_only:
                    return 0 if old_bytes == new_bytes and not modes_differ and not names_differ else 1
                if old_bytes == new_bytes and names_differ:
                    print("Renamed binary file: {} -> {}".format(git_path, new_path), flush=True)
                elif old_bytes == new_bytes and modes_differ:
                    print("Mode changed for {}: {} -> {}".format(git_path, old_mode, new_mode), flush=True)
                else:
                    print("Binary files differ: {}".format(git_path), flush=True)
                return 0
        elif len(args.files) == 2:
            fromfile, tofile = args.files
            content1 = read_file_content(fromfile)
            content2 = read_file_content(tofile)
        elif len(args.files) == 0:
            content1, content2, fromfile, tofile = parse_pair_stdin(read_stdin_content())
        else:
            raise LinediffInputError("Provide 0 files (stdin), 2 files, or 7/9 Git external diff arguments")
    except LinediffInputError as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 2

    # Detect language
    lang = args.language or detect_language(git_path if git_mode else fromfile)

    # Compute diff
    try:
        diff_lines = compute_diff(content1, content2, fromfile, tofile)
    except Exception as e:
        print(f"Error: Failed to compute diff: {e}", file=sys.stderr)
        return 2

    if args.check_only:
        return 0 if not diff_lines and not modes_differ and not names_differ else 1

    if git_mode and not diff_lines:
        if names_differ:
            print("Renamed: {} -> {}".format(git_path, new_path), flush=True)
            return 0
        if modes_differ:
            print("Mode changed for {}: {} -> {}".format(git_path, old_mode, new_mode), flush=True)
            return 0

    try:
        formatted_diff = format_diff(diff_lines, fromfile, tofile, lang, args.display)
        print(formatted_diff, flush=True)
    except BrokenPipeError:
        # Avoid another broken pipe while Python flushes stdout on shutdown.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
        return 0
    except Exception as error:
        print("Error: Failed to format diff: {}".format(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
