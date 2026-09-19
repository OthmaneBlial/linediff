# Developer API (development `main`)

The tagged 0.1.3 package predates the changes below. Python imports are available today, but the library API has not yet been declared stable. The CLI is the primary product surface.

## Exact text diff

```python
from linediff.diff import compute_diff
from linediff.render import format_unified_diff

records = compute_diff("before\n", "after\n")
patch = format_unified_diff(records, "old.txt", "new.txt") + "\n"
```

`compute_diff(left_content, right_content, left_file_path=None, right_file_path=None)` accepts decoded text and returns a list of unified-diff records. The path arguments are reserved for compatibility and do not affect the exact text calculation. Equal strings return `[]`. Final-newline and CRLF changes are retained, including `\ No newline at end of file` records where needed. `format_unified_diff` adds the requested file headers. Use the default CLI output when you need a patch for actual files; structural annotations are never an applicable patch.

`DiffEngine.lcs_linear(left, right)` supplies ordered symbol anchors for the structural view. `DiffEngine.fallback_diff(left_lines, right_lines)` expects input lines **with original line endings** (`splitlines(keepends=True)`). The old graph and shortest-path classes have been removed because they did not produce a reachable structural result.

## Python structural analysis

```python
from linediff.structural import analyze_python_changes

result = analyze_python_changes(
    "def total(items):\n    return sum(items)\n",
    "def total(items):\n    return sum(items) + 1\n",
)
for change in result.changes:
    print(change.kind, change.definition, change.old_lines, change.new_lines)
```

`StructuralResult` has `supported`, `changes`, `reason`, and `parser_backend`. A `StructuralChange` records `kind` (`added`, `removed`, `changed`, `moved`), a qualified definition name, old/new line ranges, and optional details such as `signature` or `body`. Line ranges are inclusive and one-based. Python `ast` matches definitions. Optional Tree-sitter provides source ranges when both inputs parse cleanly. Ambiguous repeated names or invalid Python return `supported=False` and a reason; callers should then show the exact text diff.

The indexed units are top-level functions/classes and direct class methods. Changes outside them remain visible in the exact text diff. A structural summary is an aid to review, not a claim of semantic equivalence.

## Optional parser API

```python
from linediff.parser import TreeSitterParser

parser = TreeSitterParser()
print(parser.get_supported_languages())
tree = parser.parse_raw("def f(): pass\n", language="python")
```

`get_supported_languages()` lists **installed and initialized** grammars. `detect_language(path)` recognizes only extensions covered by a registered grammar. `parse_raw(content, language=None, file_path=None)` returns a Tree-sitter tree or `None` if that grammar is unavailable. `parse_content(...)` returns a `ListNode`; absent grammars and parse errors produce a line-based fallback tree. `parse_to_tree(content, file_path=None)` uses a shared parser instance.

`Atom` and `ListNode` live in `linediff.model` and remain importable from `linediff.diff` for compatibility. Their `position` is a zero-based UTF-8 byte offset into the source, both for Tree-sitter nodes and line fallback nodes. The parser API does not imply that the CLI can render structural diffs for every installed grammar. See the [tested support matrix](PARSER_SUPPORT.md).

## CLI contract

`python -m linediff` and the installed `linediff` entry point share the same CLI. It accepts two file paths, a Linediff-specific stdin pair separated by a line containing only `---`, or Git external-diff's seven or nine arguments. In `--check-only` mode the exit codes are `0` same, `1` different, `2` error. Successful display exits `0`; errors go to stderr. `--display structural` is human-readable, while the default unified view is intended to be patchable for text files.

`--diagnostics` writes the actual comparison route to stderr: `exact-text`, `structural` with the parser backend, `text-fallback` with a reason, or `binary-git-status`. It does not change stdout. File input and extension detection live in `linediff.inputs` and `linediff.languages`; the formatting functions live in `linediff.render`.
