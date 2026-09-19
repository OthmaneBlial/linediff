# Usage Guide

> Tagged version 0.1.3 falls back to line diffing. Development `main` adds `--display structural` for Python and fixes exact newline comparison; these changes are not yet a verified release. The [product contract](PRODUCT.md) records the limits. The `---` separator accepted on stdin is a Linediff-specific pair format; `git diff | linediff` is unsupported.

This guide covers all the ways to use Linediff for comparing files and integrating with your workflow.

## Basic Usage

### Comparing Two Files

The simplest way to use Linediff is to compare two files:

```bash
linediff file1.py file2.py
```

This will output a unified diff showing the differences between the two files.

### Command Line Options

```bash
linediff [OPTIONS] FILE1 FILE2
```

#### Options

- `--check-only`: Check if files are identical (`0` same, `1` different, `2` input or processing error)
- `--language LANG`: Override automatic language detection
- `--display MODE`: `unified` (default), `side-by-side`, `inline`, or `structural`
- `--help`: Show help message

## Display Modes

### Unified (Default)

Traditional diff format with context:

```bash
linediff file1.py file2.py
```

Output:
```diff
--- file1.py
+++ file2.py
@@ -1,5 +1,6 @@
 def calculate_total(items):
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

### Side-by-Side

See changes next to each other:

```bash
linediff --display side-by-side file1.py file2.py
```

### Inline

Highlighted changes in unified format:

```bash
linediff --display inline file1.py file2.py
```

### Python structural view (development `main`)

This human-readable view identifies changed definitions and keeps the exact line diff underneath. It is **not** an applicable patch. For a reproducible move example from this repository:

```bash
linediff --display structural tests/fixtures/moved_function.old.py tests/fixtures/moved_function.new.py
```

The summary starts with `MOVED calculate_total [old lines 1-2; new lines 4-5]`, followed by the full unified text diff. Use `--language python` to request the same analysis for Python source stored with a non-`.py` extension. Unsupported languages fall back to text with an explicit message.

## Git Integration

### One-shot Git external diff

Run Linediff on changed files without changing Git configuration:

```bash
git -c diff.external=linediff diff --ext-diff
git -c diff.external=linediff diff --cached --ext-diff
```

The setting applies only to that command. Use `git diff --no-ext-diff` to see Git's normal output. Linediff prints readable text hunks for changed, added, deleted and renamed files, and a status line for binary changes. Git may split renames into separate deletion and addition entries with other external-diff configurations. This output is for review, not a replacement for the full Git patch format.

## CI/CD Integration

### Check-Only Mode

Use in automated pipelines to check for differences:

```bash
linediff --check-only file1.py file2.py
echo $?  # 0 = identical, 1 = different, 2 = error
```

Example in a CI script:

```bash
#!/bin/bash
if linediff --check-only generated.py expected.py; then
    echo "✅ Files match expected output"
else
    result=$?
    if [ "$result" -eq 1 ]; then
        echo "Files differ from expected output"
        exit 1
    fi
    echo "Linediff could not compare the files" >&2
    exit 2
fi
```

## Reading from Standard Input

### Git diff streams

Linediff does not parse the output of `git diff` on stdin. Use the external diff integration described above for Git; the stdin format below is specific to Linediff.

### From Stdin with Separator

Provide two UTF-8 texts via stdin with a line containing only `---` as separator:

```bash
cat > /tmp/diff_input << 'EOF'
old content here
---
new content here
EOF

linediff < /tmp/diff_input
```

## Language Override

Override automatic language detection:

```bash
linediff --language javascript file1.txt file2.txt
```

Supported languages: python, javascript, json, html, css, rust, go, java

## Advanced Usage

### Large Files

Linediff automatically optimizes for large files (>1000 nodes) by falling back to line-based diffing for performance.

### Binary Files

Linediff works with text files. For binary files, Git will handle them appropriately when configured as external diff.

### Error Handling

Linediff gracefully handles:
- Missing files
- Encoding errors
- Parser failures (falls back to line-based diffing)
- Large files (automatic optimization)

## Examples

### Python Code Review

```bash
# Compare two versions of a function
linediff old_version.py new_version.py
```

### Configuration Files

```bash
# Check JSON config changes
linediff --language json config.old.json config.new.json
```

### Web Development

```bash
# Compare HTML templates
linediff template.old.html template.new.html

# Compare CSS stylesheets
linediff styles.old.css styles.new.css
```

## Performance Tips

1. **Install only needed parsers**: `pip install tree-sitter-python tree-sitter-javascript` instead of all
2. **Let auto-detection work**: Don't override language unless necessary
3. **Use check-only mode**: For CI/CD when you only need to know if files differ
4. **Side-by-side for reviews**: Use when reviewing changes interactively

## Troubleshooting

### No Syntax Highlighting

If diffs look like regular line diffs, ensure tree-sitter parsers are installed:

```bash
pip install linediff[tree-sitter]
```

### Wrong Language Detected

Override with `--language`:

```bash
linediff --language python file.js file2.js
```

### Performance Issues

For very large files, Linediff automatically falls back to line-based diffing. If you need syntax-aware diffing for large files, consider splitting them.

## Next Steps

- [API Reference](api.md) - For programmatic usage
- [Examples](examples.md) - More detailed examples
- [Contributing](contributing.md) - How to contribute
