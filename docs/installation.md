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

On Windows, use `py -m venv .venv` and `.venv\Scripts\python -m pip install .`; the command is `.venv\Scripts\linediff --help`. A `pipx`/`uv tool` walkthrough will be added only after clean-environment checks for those installers. The base CLI has no runtime Python package dependencies.

The [quickstart](QUICKSTART.md) shows an exact observed output and the one-shot Git command. The [limits](LIMITS.md) page covers file size and complexity guards.

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
