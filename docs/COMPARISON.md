# Development comparison: Linediff, Git, Difftastic, delta

This is a **source-checkout snapshot**, not a comparison of published `0.2.0a1` downloads. It was run on 19 September 2026 on macOS 26.6 arm64 with Python 3.14.6. The exact commands, input SHA-256 values, exit codes, raw stdout and five-sample wall-time medians are in [`results.json`](../benchmarks/comparison/2026-09-19-macos-arm64/results.json) and the adjacent output files. The Linediff source was at commit `3bd793b` and reported version `0.2.0a1`. The executable releases were [Difftastic 0.71.0](https://github.com/Wilfred/difftastic/releases/tag/0.71.0) and [delta 0.19.2](https://github.com/dandavison/delta/releases/tag/0.19.2); Git was Apple Git 2.50.1.

The downloaded macOS arm64 archive SHA-256 values matched the digests in GitHub's release asset API: Difftastic `92acf8890543b6d6f436a87a7a5ec64f82a4b8dbe3a7e564c1e5cbfe60823bc7`, delta `9be36612a5a13e9e386dc498fb8e50dc87c72ee42b63db0ea05b32f99a72a69a`. These are input provenance, not an endorsement of any tool's security.

## Same input, different purposes

| Tool and command | What was observed on the frozen fixtures | Stronger use case or limit |
| --- | --- | --- |
| `git diff --no-index --no-color` | An applicable line patch with `\ No newline at end of file` on the final-newline case; no named Python definition summary. | Reference for exact file changes and Git's own diff options. |
| `linediff --display structural` | Names a changed Python definition and its signature/body, or a candidate moved definition, then includes the exact text patch. On text files it declares fallback. | A compact Python review cue plus a faithful patch; only Python has this structural CLI view. |
| `difft --color never --display inline --width 80` | Syntax-focused display; on the final-newline-only text case it reported `No changes.` On the two-function reorder it aligned the functions differently from Linediff. | Broader language-aware syntactic comparison and mature displays; see the [Difftastic manual](https://difftastic.wilfred.me.uk/introduction). It does not aim to be an applicable unified patch. |
| `delta --paging never --no-gitconfig --width 80` | A styled file diff. The raw ANSI output and a stripped text view are retained; the final-newline marker appears in its diff. | A [Git/diff pager](https://github.com/dandavison/delta) with syntax themes, word highlighting, side-by-side mode and navigation. It displays a diff rather than classifying Python definitions. |

The [`moved_function` inputs](../tests/fixtures/moved_function.old.py) reorder two unchanged functions. Linediff labels `calculate_total` as moved; [its output](../benchmarks/comparison/2026-09-19-macos-arm64/moved_function.linediff.txt) includes the exact patch. [Difftastic's output](../benchmarks/comparison/2026-09-19-macos-arm64/moved_function.difftastic.txt) aligns `calculate_total` and displays `keep` as the changed block. For a two-item reorder, either item can be described as the one that moved. Linediff's label is a useful **heuristic**, not proof of the author's intent.

On [`signature_body`](../benchmarks/comparison/2026-09-19-macos-arm64/signature_body.linediff.txt), Linediff groups a signature and body edit under `calculate_total`; Difftastic gives a syntax-oriented before/after display. On [`format_only`](../benchmarks/comparison/2026-09-19-macos-arm64/format_only.linediff.txt), Linediff says no indexed definition changed but still shows the text patch. On [`final_newline`](../benchmarks/comparison/2026-09-19-macos-arm64/final_newline.linediff.txt), its patch preserves the byte-level distinction that Difftastic's syntactic display intentionally hides. Git and delta also show the newline difference. These are observations of these four fixtures, not universal feature claims.

## Small-case timing, with limits

The following numbers are median elapsed milliseconds for a full command on this one Mac, after one excluded warm-up and with five measured runs. Each tool did different work, and delta's direct two-file command invokes its own diff path. Runner load and process startup affect these short runs. Memory was not measured. **Do not use these numbers to claim general speed superiority.**

| Fixture | Git | Linediff | Difftastic | delta |
| --- | ---: | ---: | ---: | ---: |
| `moved_function` | 25.765 | 153.884 | 45.627 | 64.990 |
| `signature_body` | 21.710 | 82.623 | 31.918 | 56.552 |
| `format_only` | 22.429 | 82.662 | 33.132 | 71.647 |
| `final_newline` | 43.528 | 108.708 | 44.691 | 94.908 |

In this snapshot, Linediff was slower than the three alternatives on all four command paths. Its Python interpreter startup and AST work are a practical cost for tiny inputs. The CI [fixture budgets](LIMITS.md) guard regressions within Linediff, but they are not comparative performance claims.

## Reproduce or refresh

Install this checkout as in [installation](installation.md). Download the named official release archives for your OS, verify their SHA-256 against the release asset digest, and extract the `difft` and `delta` executables. Then run:

```bash
python scripts/compare_tools.py --difft /path/to/difft --delta /path/to/delta --out-dir /tmp/linediff-comparison --repeats 5
```

The script refuses a nonempty output directory and checks that the installed Linediff version equals `pyproject.toml`. It isolates Git from system/global configuration, reads the same checked-in inputs, writes raw outputs (including delta's `.ansi` stream), and records fixture hashes. It does not modify the inputs or install tools. Re-run the comparison against an actually published Linediff version before using its results in release marketing; competitors, platforms and workload mix may change.
