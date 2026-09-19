# Reproducible examples

Run these commands from this checkout after following the [installation guide](installation.md). All named files are committed in `tests/fixtures/`. The [quickstart](QUICKSTART.md) pins a complete real output.

## Find a moved Python function

```bash
.venv/bin/linediff --display structural tests/fixtures/moved_function.old.py tests/fixtures/moved_function.new.py
```

The fixture has the same two functions in a different order. The view names the moved function and gives old/new lines, then shows the exact text edit. Run `--diagnostics` with the same arguments to see whether AST alone or Tree-sitter plus AST supplied the source ranges.

## Group a signature and body change

```bash
.venv/bin/linediff --display structural tests/fixtures/signature_body.old.py tests/fixtures/signature_body.new.py
.venv/bin/linediff --display side-by-side --width 80 tests/fixtures/signature_body.old.py tests/fixtures/signature_body.new.py
```

The structural view reports `CHANGED calculate_total (signature, body)`. The numbered column view marks cropped content with `…`; the unified diff gives the full lines.

## Check exact text in a script

```bash
.venv/bin/linediff --check-only tests/fixtures/final_newline.old.txt tests/fixtures/final_newline.new.txt
result=$?
echo "$result"
```

The result is `1`: only the final newline differs. The general contract is `0` same, `1` different, `2` error. A script must handle `2` separately rather than treating every nonzero status as a difference.

## Review a Git repository for one command

From a repository containing a change, with `linediff` on `PATH`:

```bash
git -c diff.external=linediff diff --ext-diff
git -c diff.external=linediff diff --cached --ext-diff
```

The setting is local to each invocation. Git supplies file operands, not a patch on stdin. The tested integration covers added, deleted, renamed, changed and binary files in a temporary Git repository. [Git limitations](usage.md#git-integration) include checkout line-ending filters.

## Compare two texts on stdin

```bash
printf 'before\n---\nafter\n' | .venv/bin/linediff
```

The separator is Linediff-specific. It does not parse `git diff` output.
