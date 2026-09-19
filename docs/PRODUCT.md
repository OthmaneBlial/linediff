# Product contract

Linediff should make changes inside Python functions easier to review in a terminal while preserving an exact, usable text diff. This is the target for the next release, not a description of version 0.1.3.

## What version 0.1.3 actually does

The current CLI compares two UTF-8 files and renders a line diff in unified, side-by-side, or inline form. `--check-only` reports whether its diff engine found changes. Git can invoke the CLI as an external diff command. The current structural graph has no path from its start vertex to its end vertex, so the result falls back to `difflib`. The line fallback also misses a difference consisting only of a final newline. The optional Tree-sitter installation and Git edge cases have not been verified. Other language names in the docs do not establish structural support.

Development `main` now fixes the final-newline and CRLF comparisons and adds a separate Python AST-based structural view. These changes have local tests but are not part of the tagged 0.1.3 release. Tree-sitter extras and other structural languages still require validation.

## Target users and promise

The first target user is a developer reviewing a Python change locally or in a Git repository. They need to find which function changed, whether a function moved, and what text actually changed. The default output must remain an exact text diff. A separate structural view may add context; it must never hide changed text or pretend to be an applicable patch.

**One-sentence value proposition:** Review Python changes by function, with a trustworthy line diff always available.

## Target behavior and output contract

| Input or mode | Target behavior | Output and exit status |
| --- | --- | --- |
| `linediff OLD NEW` | Compare two readable UTF-8 text files. | Unified patch by default; exit `0` on successful display whether same or different. |
| `--display side-by-side` | Align changed and context lines for terminal reading. | Human-readable columns; exit `0` on successful display. |
| `--display inline` | Color line changes when color is enabled. | Human-readable output; exit `0` on successful display. |
| `--display structural` (new opt-in mode) | Explain changes within Python definitions and identify supported moves. | Clearly marked as human-readable, **not** a patch. Exact unified output remains separately available. |
| `--check-only` | Compare exact source content without printing a diff. | `0` identical, `1` different, `2` input or processing error. |
| `--language python` | Override extension detection for a supported parser. | Must select the Python parser when the structural view is requested; an unknown language name is an error. |
| No file arguments | Preserve the existing `---`-separated pair input for now. | Document it as a Linediff-specific format, not Git unified diff. Preserve trailing newlines exactly. |
| Git external diff | Accept the seven arguments for ordinary changes and nine for renames or copies passed by `git diff --ext-diff`. | Render the changed pair without changing repository settings. Use a one-shot repository command so the setting disappears after the command. |

Binary files, non-UTF-8 files, directories, and missing files must be handled clearly as errors or as a documented binary status; they must never be reported as identical. Warnings and errors belong on stderr. An applicable unified patch must not contain structural annotations or ANSI escape codes. Use `--` to disambiguate filenames that start with `-`.

## Three acceptance scenarios for the Python view

These are proposed behavior, **not outputs of 0.1.3**. The fixture corpus in `tests/fixtures/` will pin each input and its expected text diff.

1. **Moved function:** two otherwise unchanged functions swap order. The view identifies a move of `calculate_total` instead of describing it solely as an unrelated deletion and addition. The unified diff still records the exact reorder.
2. **Changed signature and body:** `calculate_total(items)` becomes `calculate_total(items, tax_rate=0.08)` and its return changes. The view groups both changes under the same function and points to the changed source lines. The unified diff still shows every changed line.
3. **Changed class method:** the body of `Calculator.add` gains history tracking. The view names `Calculator.add` and separates this change from unchanged class members. The unified diff still shows the inserted lines.

## Language and fallback policy

| Language or input | Current 0.1.3 evidence | Target claim before release |
| --- | --- | --- |
| Python | Line diff observed; optional parser not verified. | Structural view only after parser and semantic output pass scenario tests. |
| JavaScript, JSON, HTML, CSS, Rust, Go, Java | Configurations exist; structural output has not been proved. | Text fallback until each grammar and rendering path has its own oracle tests. |
| TypeScript, XML, SCSS and other extensions | Some extensions map to another grammar or text. | Text fallback unless a dedicated grammar and tests justify a stronger claim. |
| Arbitrary text | `difflib` fallback observed. | Exact line diff; no syntax claim. |

## Validation rule

For each promised mode, keep both an exact text oracle and a human-review scenario. Test installation with and without the optional parser. Record measured timings and memory separately from correctness; never describe a result as faster without a reproducible comparison. When a structural result is ambiguous, expose the plain diff and state the fallback reason.
