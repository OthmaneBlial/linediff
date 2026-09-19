# Linediff

**Review Python changes by function, with an exact line diff always available.**

Linediff is a terminal CLI for comparing two UTF-8 files. Its default output is a unified text diff. The opt-in `--display structural` view names changed or moved Python definitions and includes the exact text diff below the summary. The structural view is for reading, not for applying as a patch.

> **Release status:** these changes are on development `main`. The repository has a `v0.1.3` tag, but no GitHub Release for this work has been verified. Install from this checkout to try the behavior described here. See the [roadmap](ROADMAP.md) for release gates.

## See it on a real fixture

```bash
linediff --display structural \
  tests/fixtures/moved_function.old.py \
  tests/fixtures/moved_function.new.py
```

The output identifies `MOVED calculate_total [old lines 1-2; new lines 4-5]`, then prints an `Exact text diff:` section with the full unified patch. The [quickstart](docs/QUICKSTART.md) includes the complete output, pinned by a test to the current CLI.

The default view remains a plain patch:

```bash
linediff tests/fixtures/final_newline.old.txt tests/fixtures/final_newline.new.txt
```

It distinguishes `alpha` from `alpha` followed by a final newline. The fixture suite also checks CRLF, Unicode, repeated lines, empty files, and patch application with `git apply`.

## Install this checkout

```bash
git clone https://github.com/OthmaneBlial/linediff.git
cd linediff
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/linediff --help
```

On Windows, use `py -m venv .venv` and `.venv\Scripts\python -m pip install .`. The [installation guide](docs/installation.md) covers optional grammars and developer setup. The package has no required runtime dependencies; its Python structural summary uses the standard library AST.

## Use it

| Command | Result |
| --- | --- |
| `linediff OLD NEW` | Exact unified text diff; successful display exits `0` even if files differ. |
| `linediff --display structural OLD.py NEW.py` | Python definition summary plus the exact text diff; human-readable, not an applicable patch. |
| `linediff --display side-by-side --width 80 OLD NEW` | Numbered columns with visible truncation for narrow terminals. |
| `linediff --display inline OLD NEW` | Human-readable changed lines. |
| `linediff --check-only OLD NEW` | Exit `0` same, `1` different, `2` error; no diff output. |
| `linediff --diagnostics --display structural OLD NEW` | Route, parser and fallback reason on stderr. |

`--color auto` colors human-readable views only on a terminal and respects `NO_COLOR`. Use `--color always` or `--color never` to override. The unified patch is never colored.

For a one-shot Git review without changing global configuration:

```bash
git -c diff.external=linediff diff --ext-diff
git -c diff.external=linediff diff --cached --ext-diff
```

Git invokes Linediff with its external-diff arguments. Added, deleted, changed, and renamed text files have been exercised in a temporary Git repository; binary changes get a status line. Native `git diff --no-ext-diff` remains the reference for Git's full patch and filters. See [usage](docs/usage.md) for stdin pairs and Git line-ending limits.

## What is supported

| Input | Current behavior |
| --- | --- |
| Python `.py`, `.pyw`, `.pyi` | Exact text diff; opt-in structural summary of top-level functions/classes and direct class methods. |
| Other UTF-8 text | Exact text diff; explicit fallback when structural view is requested. |
| Optional Tree-sitter grammars | Python source ranges and a parsing API; they do not add structural CLI views for other languages. |
| Binary/non-UTF-8 files | File mode returns an error; Git external mode reports binary status. |

Each text operand is capped at 4 MiB, 20,000 lines, and 200,000 characters per line. Expensive line alignment becomes an exact whole-file replacement patch; Python structural analysis has tighter limits. See [limits](docs/LIMITS.md) and the [parser support matrix](docs/PARSER_SUPPORT.md). No general speed advantage over Git or another diff tool has been measured.

## Develop and contribute

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/ruff check src/linediff tests scripts
.venv/bin/ruff format --check src/linediff tests scripts
```

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [developer API](docs/api.md), and the [product contract](docs/PRODUCT.md). For help or private vulnerability reporting, see [support](SUPPORT.md) and the [security policy](SECURITY.md). The CI workflow runs a Python and OS matrix, optional grammar profiles, formatting, linting, and wheel/sdist smoke checks; inspect its [current results](https://github.com/OthmaneBlial/linediff/actions/workflows/ci.yml) before relying on a green status.

## License

[MIT](LICENSE).
