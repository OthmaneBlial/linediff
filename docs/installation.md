# Installation from the development checkout

The current `main` branch has changes newer than the tagged 0.1.3 package. This guide installs the code in this checkout. A new public package or standalone executable has not yet been verified.

## Base CLI

Python 3.8 or newer and `pip` are required by the package metadata. The checkout installation passed GitHub Actions tests on Linux, macOS and Windows with Python 3.8–3.14 in runs `35442699106` and `35442835093`. This does not verify a public release or a standalone executable.

```bash
git clone https://github.com/OthmaneBlial/linediff.git
cd linediff
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/linediff --help
.venv/bin/linediff --display structural tests/fixtures/moved_function.old.py tests/fixtures/moved_function.new.py
```

On Windows, use `py -m venv .venv` and `.venv\Scripts\python -m pip install .`; the command is `.venv\Scripts\linediff --help`. The supported walkthrough uses `pip` in a virtual environment; `pipx` and `uv tool` have not been tested for this checkout. The base CLI has no runtime Python package dependencies.

The [quickstart](QUICKSTART.md) shows an exact observed output and the one-shot Git command. The [limits](LIMITS.md) page covers file size and complexity guards.

## Standalone candidate

`scripts/build_standalone.py` can freeze the base CLI with PyInstaller 6.22.3 on the current host. It packages no optional Tree-sitter grammar, so Python structural analysis uses the standard library AST and other languages use the text fallback. A macOS arm64 development archive was built and smoke-tested locally; standalone CI jobs on Linux, macOS and Windows succeeded in [run 35444327149](https://github.com/OthmaneBlial/linediff/actions/runs/35444327149). The manual versioned candidate workflow has not yet been run. No standalone download has been published. The [release guide](RELEASING.md) explains the candidate gate.

## Optional grammars

Python 3.10 or newer is required by the pinned Tree-sitter extras. Install from this checkout:

```bash
.venv/bin/python -m pip install '.[python]'
.venv/bin/python -m pip install '.[tree-sitter]'
```

The first command adds the Python grammar. The second adds all eight registered grammars. Only Python has a verified structural CLI view; other languages still show a text fallback. See the [parser matrix](PARSER_SUPPORT.md) for tested versions and the difference between grammar parsing and structural diffing.

## Developer setup

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/ruff check src/linediff tests scripts
.venv/bin/ruff format --check src/linediff tests scripts
```

Package metadata and optional dependencies live in `pyproject.toml`. The former `requirements.txt` contained Markdown tooling unrelated to Linediff and has been removed.

The metadata still uses the legacy `license = {text = "MIT"}` form so source builds can retain Python 3.8 support. Setuptools 77 introduced the modern SPDX field but requires Python 3.9 or newer; current setuptools prints a deprecation warning for the legacy form, with a February 2027 removal date in the build output observed on 19 September 2026. The MIT text in `LICENSE` is included in both source and wheel distributions. This warning is a known packaging tradeoff and needs a Python support decision before that deadline. Ruff is the active formatter and linter; inactive Black, isort and mypy settings have been removed.
