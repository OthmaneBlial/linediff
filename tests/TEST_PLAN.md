# Test plan

This plan implements the contract in [`docs/PRODUCT.md`](../docs/PRODUCT.md). It describes tests to add or tighten during phases 1–4; it is not a claim that the current test suite covers them.

| Area | Oracle or invariant | Planned test location |
| --- | --- | --- |
| Exact text equality | Byte-identical UTF-8 inputs are identical; any changed byte, including a final newline or CRLF, is different. | `test_unit_diff.py`, `test_cli.py` |
| Unified patch | Hunk ranges and headers are valid; applying the patch to the old file yields the new file. | `test_diff_engine.py`, new patch round-trip tests |
| CLI status | Display success is `0`; `--check-only` uses `0`/`1`/`2` for same/different/error. | `test_cli.py`, `test_error_handling.py` |
| Inputs | Pair stdin, missing file, directory, invalid UTF-8, binary, long line, repeated lines, filename beginning with `-`, pipe closure. | `test_cli.py`, `test_edge_cases.py` |
| Git | Real temporary repository: changed, added, deleted, renamed, binary, and filenames with spaces. | new `test_git_integration.py` |
| Python structure | Move, signature-and-body change, class method change; every original text change remains in unified output. | `test_diff_engine.py`, `test_parser.py` |
| Grammar selection | Optional Python-only install, extra install, no parser install, forced language, non-ASCII offsets, invalid syntax. | `test_parser.py`, `test_languages.py` |
| Packaging | Install wheel and sdist in clean environments and run `--help` plus a real comparison. | CI smoke job |
| Performance | Repeat representative small, medium and large cases; record time and resident memory with versions and platform. | `scripts/benchmark.py` |

The source fixture manifest will live in `tests/fixtures/cases.json`. Each case must name two files, the comparison rule, the expected baseline behavior, and the target behavior. The benchmark must print to stdout or write outside the checkout so running it does not alter tracked files.
