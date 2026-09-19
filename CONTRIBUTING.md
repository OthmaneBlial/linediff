# Contributing to Linediff

Linediff's current scope is exact UTF-8 text diffs and an opt-in Python definition view. A new grammar in the parser API is not, by itself, a structural CLI feature. Please describe the behavior you intend to change and keep an exact text diff available in every structural path.

## Start locally

Python 3.8+ and Git are required for the base CLI. Optional Tree-sitter extras require Python 3.10+. From a clone:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/ruff check src/linediff tests scripts
.venv/bin/ruff format --check src/linediff tests scripts
.venv/bin/python scripts/check_docs.py
```

On Windows, use `py -m venv .venv` and `.venv\Scripts\python` in place of `.venv/bin/python`. The [quickstart](docs/QUICKSTART.md) verifies the installed CLI on a committed fixture.

## Make a change

1. Check [open issues](https://github.com/OthmaneBlial/linediff/issues) and the [roadmap](ROADMAP.md). An issue label is useful only if it is actually present; the roadmap is the maintained backlog.
2. Add or update a fixture in `tests/fixtures/` for changed output. Existing `baseline/` snapshots are historical and should not be silently rewritten.
3. Add a test that would fail for the bug or feature being addressed. For exact output, check byte preservation, exit status, and patch application. For structural output, check definition names, ranges, and fallback reason.
4. Run the commands above. For parser changes, install `.[python]` or `.[tree-sitter]` in a separate environment and set `LINEDIFF_EXPECT_PARSERS=python` or `full` for the parser capability tests.
5. Update the README and relevant docs with observed behavior, then open a focused pull request. Include the command, actual output, platform/Python version, and any known limits.

The CI workflow tests the base package on Linux, macOS and Windows across the Python versions listed in the matrix; it also tests optional grammars and built distributions. A passing local test is useful evidence, while CI and published artifacts need their own verification.

## Scope of a first contribution

Good bounded tasks include improving a failing fixture, clarifying an error message, tightening an input limit test, or correcting a reproducible documentation example. A new structural language view needs a parser, a definition model, ambiguity policy, exact-diff fallback, fixture oracles, and documentation. Open an issue with a concrete example before expanding scope.

Do not put private source files, access tokens, or user data in an issue or test fixture. For a suspected vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening a public issue. For ordinary usage questions, use [GitHub Issues](https://github.com/OthmaneBlial/linediff/issues) with the question template.
