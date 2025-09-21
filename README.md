# Linediff

[![PyPI version](https://badge.fury.io/py/linediff.svg)](https://pypi.org/project/linediff/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/OthmaneBlial/linediff/actions/workflows/ci.yml/badge.svg)](https://github.com/OthmaneBlial/linediff/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/OthmaneBlial/linediff/branch/main/graph/badge.svg)](https://codecov.io/gh/OthmaneBlial/linediff)
[![Downloads](https://pepy.tech/badge/linediff)](https://pepy.tech/project/linediff)

A lightweight, syntax-aware diff tool for Python with tree-sitter integration. Linediff understands code structure using tree-sitter parsers, providing more meaningful diffs than traditional line-based tools.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Git Integration](#git-integration)
- [Supported Languages](#supported-languages)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Performance](#performance)
- [Development](#development)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Syntax-aware diffing**: Uses tree-sitter parsers to understand code structure
- **Multiple display modes**: unified, side-by-side, and inline views
- **Git integration**: Can be used as external diff tool
- **Multi-language support**: Python, JavaScript, JSON, HTML, CSS, Rust, Go, Java
- **Automatic language detection**: Based on file extensions
- **Robust fallbacks**: Falls back to line-based diffing when needed
- **Check-only mode**: For CI/CD pipelines (exit code indicates if files differ)
- **Color output**: ANSI color codes for better readability
- **Stdin support**: Can read diff input from stdin

## 🚀 Quick Start

### Get Linediff in Seconds

**From PyPI (Easiest Way):**
```bash
pip install linediff
```

**From Source (For Contributors):**
```bash
git clone https://github.com/OthmaneBlial/linediff.git
cd linediff
pip install -e .
```

### Supercharge with Syntax Parsers

Unlock the full power of syntax-aware diffing:

```bash
# Get all language parsers
pip install linediff[tree-sitter]

# Or pick your favorites
pip install tree-sitter-python tree-sitter-javascript tree-sitter-json
```

## 🎯 Usage

### Basic Diff Magic

Compare any two files with intelligent diffing:

```bash
linediff file1.py file2.py
```

See the difference? It's not just lines – it's code structure! 🎉

### Git Integration

Linediff can be used as Git's external diff tool:

#### Global Setup
```bash
git config --global diff.external linediff
```

#### Per-Language Configuration
```bash
git config diff.python.command "linediff --language python"
git config diff.python.binary false
```

#### Project Configuration
Add to `.gitattributes`:
```gitattributes
*.py diff=python
*.js diff=javascript
*.json diff=json
```

### Check-Only Mode

For CI/CD pipelines, use `--check-only` to check if files differ without output:

```bash
linediff --check-only file1.py file2.py
echo $?  # 0 = identical, 1 = different
```

### Language Override

Override automatic language detection:

```bash
linediff --language javascript file1.txt file2.txt
```

### Display Modes

Choose how your diffs are displayed:

**Unified (default)** - Traditional diff format:
```bash
linediff file1.py file2.py
```

**Side-by-side** - See changes next to each other with color coding:
```bash
linediff --display side-by-side file1.py file2.py
```

**Inline** - Changes highlighted with ANSI colors:
```bash
linediff --display inline file1.py file2.py
```

### Reading from Stdin

Pipe diff output through linediff:

```bash
git diff | linediff
```

Or provide content via stdin with separator:

```bash
cat > /tmp/diff_input << 'EOF'
old content here
---
new content here
EOF

linediff < /tmp/diff_input
```

## 🌍 Language Support

**Supported Languages:**

| Language | Extensions |
|----------|------------|
| Python | `.py`, `.pyw`, `.pyi` |
| JavaScript | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs` |
| JSON | `.json`, `.jsonc` |
| HTML | `.html`, `.htm`, `.xml` |
| CSS | `.css`, `.scss`, `.sass`, `.less` |
| Rust | `.rs` |
| Go | `.go` |
| Java | `.java` |

For unsupported languages, Linediff falls back to line-based diffing using Python's difflib.

## 🎨 See Linediff in Action

### Python Function Evolution

**Before:**
```python
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
```

**After:**
```python
def calculate_total(items, tax_rate=0.08):
    """Calculate total with tax."""
    subtotal = sum(item.price for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
```

**Diff output:**
```diff
--- old.py
+++ new.py
@@ -1,5 +1,6 @@
-def calculate_total(items):
-    total = 0
-    for item in items:
-        total += item.price
-    return total
+def calculate_total(items, tax_rate=0.08):
+    """Calculate total with tax."""
+    subtotal = sum(item.price for item in items)
+    tax = subtotal * tax_rate
+    return subtotal + tax
```

### JavaScript Object Makeover

**Before:**
```javascript
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
  retries: 3
};
```

**After:**
```javascript
const config = {
  apiUrl: "https://api.example.com",
  timeout: 10000,
  retries: 3,
  headers: {
    "Authorization": "Bearer token"
  }
};
```

**Diff output:**
```diff
--- config.js
+++ config.js
@@ -1,5 +1,8 @@
 const config = {
   apiUrl: "https://api.example.com",
-  timeout: 5000,
+  timeout: 10000,
   retries: 3,
+  headers: {
+    "Authorization": "Bearer token"
+  }
 };
```

### JSON Config Transformation

**Before:**
```json
{
  "database": {
    "host": "localhost",
    "port": 5432
  },
  "features": ["auth", "logging"]
}
```

**After:**
```json
{
  "database": {
    "host": "prod-db.example.com",
    "port": 5432,
    "ssl": true
  },
  "features": ["auth", "logging", "metrics"]
}
```

**Diff output:**
```diff
--- config.json
+++ config.json
@@ -1,6 +1,8 @@
 {
   "database": {
-    "host": "localhost",
+    "host": "prod-db.example.com",
     "port": 5432,
+    "ssl": true
   },
   "features": ["auth", "logging", "metrics"]
 }
```

## How It Works

Linediff uses a two-phase approach:

1. **Syntax Parsing**: Tree-sitter parsers convert source code into abstract syntax trees (ASTs)
2. **Structural Diffing**: A graph-based algorithm finds optimal matches between AST nodes
3. **Fallback**: For large files or unsupported languages, falls back to standard difflib

The diff engine implements Dijkstra's algorithm on a graph where nodes represent code elements and edges represent possible matches, insertions, or deletions.

## Performance

- **Small files**: Syntax-aware diffing provides more meaningful results
- **Large files**: Automatically falls back to line-based diffing for performance
- **Memory efficient**: Tree parsing is done on-demand with caching
- **Fast startup**: Parser instances are cached for repeated operations

## 🛠️ Development

### Get Started Contributing

**Set up your dev environment:**

```bash
git clone https://github.com/OthmaneBlial/linediff.git
cd linediff
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run the Test Suite

```bash
pytest  # Fast, comprehensive testing
```

### Comprehensive Testing Suite

For an interactive testing experience with various scenarios and display modes:

```bash
./test_linediff.sh
```

This provides a menu-driven interface to test different file types, languages, and display modes with real example files.

### Building Documentation

```bash
# Generate documentation (if applicable)
```

### Code Quality

```bash
# Run linting
flake8 src/

# Run type checking
mypy src/

# Format code
black src/
```


## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/api.md)
- [Examples](docs/examples.md)
- [FAQ](docs/faq.md)
- [Contributing Guide](CONTRIBUTING.md)

For online documentation, visit [https://othmaneblial.github.io/linediff/](https://othmaneblial.github.io/linediff/).

## 🤝 Contributing

**Join the revolution!** We love contributions from developers like you.

Check out our [Contributing Guide](CONTRIBUTING.md) for the full details.

### Quick Contribution Flow

1. 🍴 Fork the repository
2. 🌿 Create a feature branch: `git checkout -b feature/amazing-idea`
3. 💻 Make your awesome changes
4. ✅ Add comprehensive tests
5. 🚀 Ensure all tests pass: `pytest`
6. 📤 Submit a pull request

### Add a New Language

**Expand Linediff's universe:**

1. Add tree-sitter parser to `pyproject.toml`
2. Configure language support in `parser.py`
3. Write tests for the new language
4. Update this README with examples

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

**Standing on the shoulders of giants:**

- Powered by [Tree-sitter](https://tree-sitter.github.io/) for syntax parsing
- Built with [Python](https://www.python.org/) and cutting-edge algorithms
- Community-driven development with ❤️