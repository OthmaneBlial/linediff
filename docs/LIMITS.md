# Input and complexity budgets (development `main`)

Linediff reads UTF-8 text. Each operand is limited to 4 MiB encoded bytes, 20,000 lines, and 200,000 characters per line. The legacy stdin pair is capped at 8 MiB before decoding. Inputs outside these bounds exit with code `2` and a reason on stderr. Git binary operands use the same byte cap; ordinary binary files are rejected as text.

The CLI rejects terminal control and bidi override characters in ordinary text and path labels. LF, tabs, and CRLF are allowed; bare CR is rejected. This prevents an untrusted file from injecting terminal escapes into an otherwise applicable patch. Git external mode reports terminal-unsafe text by status without printing its contents. The lower-level `compute_diff` API accepts strings directly, so callers rendering its records should apply their own terminal policy.

File operands must resolve to regular files. A symlink to a regular file is allowed and remains subject to the same byte cap; directories, devices and named pipes are rejected. Reads use a nonblocking file descriptor and check its type again after opening, so a swapped FIFO does not leave the CLI waiting for a writer. The CLI does not execute compared content.

The line matcher uses detailed alignment only when the product of the two line counts is at most 8 million. Above that threshold it emits a whole-file replacement patch. That patch preserves content and line endings, but it is less useful for review. Python structural analysis uses an additional 1 MiB and 500 top-level definition budget; above either it reports a text fallback and retains the exact text diff. The Tree-sitter API rejects inputs above 4 MiB and falls back to lines if tree conversion exceeds Python's recursion limit.

These are conservative resource guards, not measured guarantees of wall time on every input. The checked-in corpus contains 2,000-line, 100,000-character-line, repeated-line, CRLF, Unicode, and binary cases. `tests/test_limits.py` checks all limits and applies a 3,000-line whole-file patch with `git apply`. An earlier local measurement (macOS 26.6 arm64, Python 3.14.6, three repeats) gave a 2.1 ms median engine time and 23.42 MiB maximum process RSS for the 2,000-line fixture. Tests passed on Linux, macOS and Windows in GitHub Actions runs `35442699106` and `35442835093`; time and memory budgets on those CI machines were not measured.

The newer installed-package benchmark at commit `559f74b` (same macOS/Python, three repeats) measured the 2,000-line fixture at 3.683 ms median engine time, 199.766 ms median CLI time and 23.8 MiB maximum worker RSS. The first cross-platform CI measurement ([run 35444327149](https://github.com/OthmaneBlial/linediff/actions/runs/35444327149), commit `0b08668`, Python 3.12, three repeats per case) returned the following for the five checked-in fixtures. Download the per-OS `linediff-benchmark-*` artifacts from that run for the complete JSON.

| OS runner | Slowest median CLI call | Highest worker peak RSS |
| --- | ---: | ---: |
| Ubuntu | 73.885 ms | 18.40 MiB |
| macOS arm64 | 90.225 ms | 22.03 MiB |
| Windows | 105.909 ms | 22.17 MiB |

`scripts/benchmark.py` measures each engine call in a fresh process and each full `--check-only` CLI call separately. The memory column is the **engine worker**, not the CLI peak. CI now fails if any fixture exceeds a 500 ms median CLI call or a 64 MiB worker peak RSS, and has a 15-second timeout for each subprocess. These deliberately broad regression budgets allow runner variability; they are not a latency or memory guarantee for arbitrary input. Run `python scripts/benchmark.py --repeats 3 --timeout-seconds 15 --max-cli-ms 500 --max-worker-rss-mib 64` in an installed environment to reproduce the gate. Windows peak worker memory requires `psutil==7.2.2`; without it the JSON field is `null` and a requested memory budget fails. These fixture measurements do not imply a bound for every accepted 4 MiB file.
