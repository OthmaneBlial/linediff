# Reproducible baseline before the diff engine changes

This is a local measurement of commit `8020a37` with the fixture corpus subsequently added in phase 0.2. It is not a publication benchmark, cross-platform claim, or comparison with another project.

## Corpus

[`tests/fixtures/cases.json`](../tests/fixtures/cases.json) lists 15 cases, their input paths and byte counts, comparison rule, expected target behavior, and observed version 0.1.3 exit codes. Nonempty original outputs are saved in `tests/fixtures/baseline/*.stdout` or `*.stderr`; a `null` path means empty output. Both input files for each case are checked in. The `long_line` case has one 100,000-character line; `large` has 2,000 lines per side.

Observed with `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m linediff [--check-only] OLD NEW`:

| Case | Old/new bytes | Exact change? | Baseline `--check-only` | Target assertion |
| --- | ---: | --- | ---: | --- |
| `replace` | 11 / 12 | Yes | 1 | Changed line preserved |
| `insert_delete` | 14 / 20 | Yes | 1 | Deletion and additions preserved |
| `moved_function` | 59 / 59 | Yes | 1 | Function move named; exact patch retained |
| `signature_body` | 50 / 82 | Yes | 1 | Signature/body grouped by function |
| `class_method` | 65 / 100 | Yes | 1 | Method identified |
| `format_only` | 30 / 26 | Yes | 1 | No invented semantic change |
| `repeated_lines` | 19 / 22 | Yes | 1 | Patch applies unambiguously |
| `unicode` | 31 / 31 | Yes | 1 | UTF-8 and source ranges preserved |
| `final_newline` | 5 / 6 | Yes | **0 (incorrect)** | Distinguish missing newline |
| `crlf` | 13 / 11 | Yes | **0 (incorrect)** | Distinguish CRLF from LF |
| `empty_same` | 0 / 0 | No | 0 | Identical |
| `empty_to_text` | 0 / 6 | Yes | 1 | Addition from empty file |
| `long_line` | 100001 / 100001 | Yes | 1 | Exact change and bounded cost |
| `large` | 32890 / 32888 | Yes | 1 | Exact change and bounded cost |
| `binary` | 3 / 3 | Yes | **1 (error also uses 1)** | Explicit binary/error status |

## Timing and memory

Command: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/benchmark.py --repeats 5`. Platform: macOS 26.6 arm64, Python 3.14.6. The script starts a fresh process for each engine sample and measures the CLI separately with `--check-only`. Times below are medians over five runs. Resident memory is the maximum per-case process peak reported by `resource.getrusage`; it includes Python startup and imports. Results are sensitive to hardware and system load.

| Case | Median engine ms | Median CLI ms | Maximum peak RSS MiB |
| --- | ---: | ---: | ---: |
| `replace` | 0.220 | 169.424 | 23.83 |
| `moved_function` | 0.246 | 157.663 | 23.77 |
| `signature_body` | 0.187 | 145.586 | 23.89 |
| `long_line` | 1.013 | 172.791 | 24.53 |
| `large` | 17.495 | 198.920 | 25.03 |

The engine measurement invokes `compute_diff`; the CLI measurement includes startup and file reading. The script prints JSON to stdout and writes no files. These numbers do **not** prove syntax-aware performance: the current engine falls back to line diffing.

## Revalidation

1. Run `python3 scripts/benchmark.py --repeats 5` from the repository root with `PYTHONDONTWRITEBYTECODE=1`.
2. Compare each current result with the corresponding fixture and baseline snapshot. Keep snapshots as historical evidence; add separate target assertions rather than changing them to match new behavior.
3. Record Python, OS, architecture, commit, repeat count, and raw command before using any measurement in public documentation.
