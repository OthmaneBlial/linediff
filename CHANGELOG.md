# Changelog
All notable changes to this project will be documented here.

## Unreleased (`main`, not published)

- Preserve CRLF and final-newline differences in applicable unified patches; distinguish `--check-only` results from errors.
- Add an opt-in Python definition view for moves, signature/body changes and direct class methods, with explicit text fallback and diagnostics.
- Validate optional Tree-sitter installation profiles; remove unreachable graph diff code.
- Handle Git external diff renames, additions, deletions, binary changes and paths with spaces in integration tests.
- Bound input sizes and expensive alignment; improve terminal color, width and line-number handling.
- Add fixture corpus, installation smoke checks and a multi-OS CI matrix. Distribution and release publication remain separate gates.
- Guard terminal output against unsafe file and Git diff content; replace the release uploader with a read-only candidate preparation flow.
- Reject non-regular file operands and add known-vulnerability and Git history secret checks to CI.
- Add a candidate-only standalone CLI build and archive smoke checks for the supported host OSes.
- Measure benchmark fixtures with per-process timeouts and cross-platform CI artifacts.

## [0.1.3] - 2025-11-15

- Fix ReadMe

## [0.1.2] - 2025-11-15

- Add script to build on pypi

## [0.1.1] - 2025-11-15

- Init
