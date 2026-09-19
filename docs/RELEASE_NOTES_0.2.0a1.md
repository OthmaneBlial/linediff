# Linediff 0.2.0a1 — candidate notes (not published)

These notes describe the current candidate source on `main`. They are a draft for maintainer review, **not** a GitHub Release, PyPI announcement, or download link. The exact commit and artifact hashes must be filled from the final approved candidate build before publication.

## What a developer gets

- An exact UTF-8 unified text diff that preserves CRLF and final-newline differences. The fixture suite applies generated patches and checks the resulting bytes.
- An opt-in `--display structural` view that groups changed Python definitions and names a possible moved function, while retaining the exact text diff beneath it. The move label uses source-order anchors and can be ambiguous when two definitions exchange places.
- One-shot `git diff --ext-diff` use without persistent Git configuration, including tested additions, deletions, renames, binary status and paths containing spaces.
- Human-readable side-by-side and inline views with line numbers, width limits and controlled color. `--diagnostics` reports the route or fallback on stderr.
- A base CLI with no runtime package dependencies. Optional Tree-sitter grammar extras expose parsing APIs; only Python has a verified structural CLI view.

## Compatibility and limits

The base package metadata sets a minimum of Python 3.8. CI has verified 3.8–3.14; newer versions are unverified. Optional grammar extras require Python 3.10 or newer. CI tests the base package across Linux, macOS and Windows on all seven listed Python versions, and downloads the built wheel/sdist for smoke tests on each OS with Python 3.8 and 3.14. Standalone candidate archives exclude the optional grammars. No public release or hardware-user validation follows from these jobs.

File operands must be regular UTF-8 text, up to 4 MiB and 20,000 lines each. The CLI rejects unsafe terminal control characters; Git external mode reports a status for binary or unsafe content. Expensive line alignment becomes a whole-file exact patch, and Python structural analysis has tighter bounds. See [limits](LIMITS.md), [parser support](PARSER_SUPPORT.md), and the [product contract](PRODUCT.md).

## Behavior changes from tagged 0.1.3

`--check-only` now returns `0` for equal files, `1` for different files and `2` for input or calculation errors. The default display mode returns `0` when it prints a diff. The old `git diff | linediff` example has been removed because stdin accepts a specific two-file separator format, not an arbitrary Git patch. Scripts depending on the former error code or that pipe example must update.

## Validation before any publication

- Local final candidate dry run and build on a clean commit, with tests, Ruff, documentation links, `twine check`, archive install smoke tests and SHA-256 checksums.
- Green GitHub Actions CI for **that same commit**, including the six archive smoke jobs, three standalone OS jobs, security job and benchmark budgets.
- Optional read-only release-candidate workflow, followed by download and inspection of its temporary artifacts. It has not yet been dispatched for this version.
- Review of the About description, tag, target accounts, release notes, platform labels and publication permissions with the maintainer. Public publishing requires separate authorization and verification.

There is no current claim of five external user trials, a GitHub Release, a PyPI upload, a published standalone executable or the final product video. Those gates remain in the [roadmap](../ROADMAP.md).
