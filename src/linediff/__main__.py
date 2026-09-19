#!/usr/bin/env python3
"""CLI entry point for linediff."""

import argparse
import sys
import os
from .diff import compute_diff
from .inputs import LinediffInputError, read_file_content, read_git_bytes, read_stdin_content, parse_pair_stdin
from .languages import KNOWN_LANGUAGES, detect_language
from .render import format_diff, format_unified_diff, format_structural_diff
from .structural import analyze_python_changes
from .limits import DiffLimitError


def main() -> int:
    parser = argparse.ArgumentParser(description="A lightweight line diff tool with Git integration.")
    parser.add_argument("files", nargs='*', help="Two files or Git external diff arguments")
    parser.add_argument("--check-only", action="store_true", help="Check if files are identical (0 same, 1 different, 2 error)")
    parser.add_argument("--language", choices=sorted(KNOWN_LANGUAGES), help="Override language detection")
    parser.add_argument("--display", choices=['unified', 'side-by-side', 'inline', 'structural'], default='unified',
                       help="Display mode for diffs (default: unified)")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Report the actual comparison route and fallback on stderr")
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
                if args.diagnostics:
                    print("Diagnostic: route=binary-git-status", file=sys.stderr)
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
    except (LinediffInputError, DiffLimitError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 2

    # Detect language
    lang = args.language or detect_language(git_path if git_mode else fromfile)

    # Compute diff
    try:
        diff_lines = compute_diff(content1, content2, fromfile, tofile)
    except DiffLimitError as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: Failed to compute diff: {e}", file=sys.stderr)
        return 2

    if args.check_only:
        if args.diagnostics:
            print("Diagnostic: route=exact-text; language={}".format(lang), file=sys.stderr)
        return 0 if not diff_lines and not modes_differ and not names_differ else 1

    if git_mode and not diff_lines:
        if names_differ:
            print("Renamed: {} -> {}".format(git_path, new_path), flush=True)
            return 0
        if modes_differ:
            print("Mode changed for {}: {} -> {}".format(git_path, old_mode, new_mode), flush=True)
            return 0

    try:
        if args.display == 'structural':
            analysis = analyze_python_changes(content1, content2) if lang == 'python' else None
            if args.diagnostics:
                if analysis is None:
                    route = "text-fallback; reason=no verified structural view for '{}'".format(lang)
                elif analysis.supported:
                    route = "structural; parser={}".format(analysis.parser_backend)
                else:
                    route = "text-fallback; reason={}".format(analysis.reason)
                print("Diagnostic: route={}; language={}".format(route, lang), file=sys.stderr)
            formatted_diff = format_structural_diff(
                diff_lines, fromfile, tofile, lang, content1, content2, analysis
            )
        else:
            if args.diagnostics:
                print("Diagnostic: route=exact-text; language={}".format(lang), file=sys.stderr)
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
