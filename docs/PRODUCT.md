# Product contract for development `main`

**Promise:** Review Python changes by function, with a trustworthy line diff always available.

The primary user compares local Python revisions, often through Git. A named definition and its source range can make a move or grouped change easier to find. The exact text edit must remain visible and patchable in the default mode. Version `v0.1.3` predates the current implementation; no new release has been verified.

## CLI behavior

| Input or mode | Behavior | Exit status |
| --- | --- | --- |
| `linediff OLD NEW` | Unified diff of UTF-8 text, preserving CRLF and final-newline changes. | `0` when successfully displayed, whether changed or not; `2` on error. |
| `--display structural` | Python AST summary of indexed definitions, then exact text diff. Other languages and invalid/ambiguous Python show a fallback reason. Human-readable, not a patch. | `0` when displayed; `2` on error. |
| `--display side-by-side` | Numbered columns, paired removal/addition rows, visible crop marker and summary. | `0` when displayed; `2` on error. |
| `--display inline` | Human-readable diff with optional color. | `0` when displayed; `2` on error. |
| `--check-only` | Compare without output. | `0` identical, `1` different, `2` error. |
| No file arguments | Two UTF-8 texts separated by a line containing only `---`; not a Git patch stream. | Same display/check contract. |
| Git external diff | Seven or nine Git arguments, including renames, additions, deletions and binary status. | `0` when displayed, `1` for a changed `--check-only`, `2` on error. |

`--diagnostics` reports the actual text, structural, or fallback route on stderr. `--language python` selects Python analysis for a non-`.py` filename; a language name alone never claims parser support. `--` disambiguates filenames starting with a dash.

## Structural scope

Python's standard AST matches top-level functions/classes and direct class methods by qualified name and source order. The optional Tree-sitter Python grammar can supply byte-accurate source ranges; without it, AST ranges are used. LCS anchors flag moved top-level definitions. Repeated definition names, syntax errors, and resource budgets cause an explicit text fallback. Code outside indexed definitions is still present in the exact text diff. The view does not establish semantic equivalence.

The fixture corpus exercises a moved function, a changed signature and body, and a changed class method. `tests/test_structural.py` checks names, change kinds, details, and ranges. `tests/test_exact_diff.py` applies generated patches to the text fixture corpus. [Parser support](PARSER_SUPPORT.md) distinguishes installed grammars from CLI structural views.

## Boundaries

The base CLI has no required runtime packages. It accepts UTF-8 text; regular binary, non-UTF-8, directory and missing-file inputs fail with a readable error. Git external mode reports a status for binary changes. Each operand has [input and complexity limits](LIMITS.md); large comparisons may use a whole-file replacement patch. The current library API is importable but is not declared stable. Release, download, provider adoption, and speed claims require separate verification.
