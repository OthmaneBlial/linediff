# Changelog
All notable changes to this project will be documented here.

## Unreleased (`main`, not published)

No changes since the current candidate source snapshot.

## [0.2.0a1] - 2026-09-19

Candidate source only. No tag, GitHub Release, PyPI upload, or public standalone download is implied by this section.

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
- Add real terminal capture assets for structural, column and inline views, with test-checked provenance.
- Add a real Git external-diff capture and reproducible terminal output tests, including LF fixtures for Windows.
- Add four isolated mutation probes and subprocess-aware branch coverage evidence for critical paths.
- Align package metadata with the tested Python matrix and document the Python 3.8 license-metadata tradeoff.
- Download and smoke-test the built wheel and source archive on Linux, macOS and Windows at the Python 3.8 and 3.14 support boundaries.
- Add a dated, reproducible development comparison with Git, Difftastic and delta, including raw outputs and measured limitations.
- Remove an obsolete PyPI-token environment template from the former release process.
- Gate candidate standalone builds on cross-platform smoke tests of the wheel and source archive; prepare consented user-trial protocol and draft candidate release notes.

## [0.1.3] - 2025-11-15

- Fix ReadMe

## [0.1.2] - 2025-11-15

- Add script to build on pypi

## [0.1.1] - 2025-11-15

- Init
