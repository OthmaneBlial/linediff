# Test evidence for development `main`

The regular suite exercises the package and the CLI as an installed module. A passing test only proves the covered scenarios; the four deliberate fault probes below test whether specific critical assertions would catch regressions.

Run `python scripts/mutation_probe.py` after installing this checkout and `pytest`. The script copies `src/linediff` and `tests` into a temporary directory, verifies four baseline tests pass, then injects one fault at a time. It leaves the working tree unchanged. On macOS arm64 with Python 3.14.6 on 19 September 2026, all four baseline tests passed and all four faults were rejected by an assertion:

| Fault injected into temporary copy | Test that failed |
| --- | --- |
| Ignore the final LF when checking exact equality | `test_exact_change_detection` |
| Return `0` instead of `1` for changed files under `--check-only` | `test_check_only_distinguishes_same_change_and_error` |
| Ignore the forced `--language` choice | `test_language_override_selects_python_view_for_text_extension` |
| Disable the Python structural route | `test_diagnostics_identify_route_only_on_stderr` |

These are four selected mutations, not a general mutation score. CI ran them successfully on Ubuntu/Python 3.12 in [run 35445154639](https://github.com/OthmaneBlial/linediff/actions/runs/35445154639), alongside the normal cross-platform suite.

## Branch coverage

With `coverage.py 7.16.1`, the local full suite passed when measured with subprocess tracing. Use a temporary coverage configuration containing `source = linediff`, `branch = true`, `parallel = true`, and `patch = subprocess`; run `coverage run --rcfile CONFIG -m pytest -q`, then `coverage combine --rcfile CONFIG` and `coverage report --rcfile CONFIG -m`. Keep the coverage data file outside the checkout. The run on 19 September 2026 combined 58 nonempty process files; its line-plus-branch report was:

| Module | Combined coverage |
| --- | ---: |
| `diff.py` | 94% |
| `inputs.py` | 94% |
| `limits.py` | 100% |
| `parser.py` | 85% |
| `structural.py` | 84% |
| `__main__.py` | 77% |
| All `linediff` modules | 87% |

The suite skipped the Git for Windows null-operand test on this Mac; GitHub Actions exercises it on Windows. The missing paths include uncommon CLI write errors and ambiguous or malformed structures. Coverage does not establish correctness by itself; the exact patch round-trips, Git integration tests and mutation probes check behavior separately. The report is a local measurement, not a cross-platform coverage result.
