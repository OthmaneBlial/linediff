# Parser support and verified installation profiles

The structural CLI view currently explains **Python definitions only**. It works with the standard-library Python AST in the base installation. Optional Tree-sitter packages provide a second parser for Python source ranges and a parsing API for other grammars; installing a grammar does **not** turn that language into a structural diff view.

## Installation profiles

| Command | Expected parser availability | Structural CLI behavior |
| --- | --- | --- |
| `pip install .` | No Tree-sitter grammars | Python definitions via `ast`; other languages text fallback |
| `pip install '.[python]'` | Python grammar only | Python AST matching with Tree-sitter UTF-8 source ranges |
| `pip install '.[tree-sitter]'` | Eight registered grammars | Same verified Python structural view; other languages still text fallback |

The base package declares Python 3.8 or later. The pinned optional Tree-sitter packages used here declare Python **3.10 or later**; `.[python]` and `.[tree-sitter]` should therefore be installed on Python 3.10+. The base Python 3.8/3.9 path is planned for CI validation, not claimed from this local machine.

The optional versions tested on macOS 26.6 arm64 with Python 3.14.6 are `tree-sitter==0.26.0`, `tree-sitter-python==0.25.0`, `tree-sitter-javascript==0.25.0`, `tree-sitter-json==0.24.8`, `tree-sitter-html==0.23.2`, `tree-sitter-css==0.25.0`, `tree-sitter-rust==0.24.2`, `tree-sitter-go==0.25.0`, and `tree-sitter-java==0.23.5`. The [official Python binding example](https://github.com/tree-sitter/py-tree-sitter/blob/master/README.md) uses `Language(grammar.language())` with `Parser(language)`, which matches the API exercised here.

## Grammar versus structural-view support

| Language | Tested optional grammar | CLI structural explanation |
| --- | --- | --- |
| Python `.py`, `.pyw`, `.pyi` | Yes | Yes: top-level functions/classes and direct class methods |
| JavaScript `.js`, `.jsx`, `.mjs`, `.cjs` | Yes | Text fallback |
| JSON `.json` | Yes | Text fallback |
| HTML `.html`, `.htm` | Yes | Text fallback |
| CSS `.css` | Yes | Text fallback |
| Rust `.rs` | Yes | Text fallback |
| Go `.go` | Yes | Text fallback |
| Java `.java` | Yes | Text fallback |
| TypeScript, JSONC, XML, SCSS and other extensions | No dedicated grammar in this package | Text fallback |

Each optional grammar is imported independently. The `TreeSitterParser.get_supported_languages()` API returns only grammars that can actually be initialized. Invalid source or absent grammar falls back to a line tree without printing diagnostic text into the diff. Python structural analysis uses Tree-sitter byte positions only when both inputs parse cleanly; otherwise it uses Python AST positions. A Python syntax error causes the structural view to show its fallback reason and the exact line diff.

## Local verification completed

Three isolated Python 3.14 environments were installed from this checkout, one per profile. `LINEDIFF_EXPECT_PARSERS=none|python|full python -m unittest discover -s tests -p test_parser_capabilities.py` passed in each matching environment. The full environment initialized and parsed samples in all eight grammars. The Python-only environment showed `['python']` and preserved source ranges for `café` and `🌍` using UTF-8 byte offsets. This does not establish wheel availability or runtime behavior on Linux, Windows, Python 3.8/3.9, or other architectures.
