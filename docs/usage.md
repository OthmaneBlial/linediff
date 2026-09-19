# Usage on development `main`

Install this checkout as shown in [installation](installation.md). The `v0.1.3` tag predates the behavior below. The [quickstart](QUICKSTART.md) shows a complete, test-pinned output.

## Compare files

```bash
linediff OLD NEW
linediff --display structural OLD.py NEW.py
linediff --display side-by-side --width 80 OLD NEW
linediff --display inline OLD NEW
```

The default unified view preserves UTF-8 text, CRLF, and final-newline changes. It is the only view intended as an applicable patch. `structural` summarizes indexed Python definitions, and includes the exact text diff underneath. Unsupported languages or invalid Python show a fallback reason. The column view pairs adjacent removals/additions, shows line numbers, and marks cropped text with `…`.

Successful display exits `0` even when files differ. For a comparison without diff output:

```bash
linediff --check-only OLD NEW
```

Here `0` means identical, `1` different, and `2` error. Binary, non-UTF-8, directory, missing, and over-budget file operands return an error on stderr. Prefix `--` before filenames that begin with `-`.

`--language python` forces Python structural analysis for a file without a Python suffix. Other language names describe extension routing, not a promise of structural support. `--diagnostics` reports the actual route and fallback reason on stderr. See [parser support](PARSER_SUPPORT.md) and [limits](LIMITS.md).

## Color and width

`--color auto` is the default for the human-readable inline and side-by-side views. It uses a terminal, respects `NO_COLOR`, and emits no ANSI color into a pipe. `--color always` and `--color never` override auto. The unified patch never has color. `--width N` bounds side-by-side output in terminal cells, with a minimum of 40; omitted width uses the detected terminal width.

## Git integration

Run Linediff as Git's external diff for one invocation:

```bash
git -c diff.external=linediff diff --ext-diff
git -c diff.external=linediff diff --cached --ext-diff
```

This does not alter local or global Git config. Git invokes Linediff with seven arguments for ordinary changes and nine for renames/copies. Text files are shown as a unified comparison, binary changes as a status line, and identical Git object IDs on both sides of a rename as a rename status. Use `git diff --no-ext-diff` for the native full Git patch.

Git's filters can make temporary old/new operand bytes differ from the normalized patch. Linediff compares those bytes exactly for changed objects. A same-object rename is recognized from Git's object IDs despite checkout line-ending differences. This behavior has integration tests; inspect the [current CI run](https://github.com/OthmaneBlial/linediff/actions/workflows/ci.yml) for platform results.

## Standard input

With no file arguments, Linediff accepts two UTF-8 texts separated by a line containing only `---`:

```bash
printf 'before\n---\nafter\n' | linediff
```

This is a Linediff pair format. `git diff | linediff` is unsupported because a Git patch stream is a different format. The pair parser preserves each side's line endings; the total input is capped at 8 MiB.
