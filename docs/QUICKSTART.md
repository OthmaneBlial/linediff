# Five-minute source checkout walkthrough

These commands use the current checkout, which contains changes newer than the tagged 0.1.3 package. Run them from the repository root. They do not change global Git configuration.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/linediff --display structural tests/fixtures/moved_function.old.py tests/fixtures/moved_function.new.py
```

On Windows, replace `.venv/bin/` with `.venv\Scripts\`. The structural output on this fixture begins:

```text
Structural view (human-readable; not an applicable patch)
MOVED calculate_total [old lines 1-2; new lines 4-5]

Exact text diff:
--- tests/fixtures/moved_function.old.py
+++ tests/fixtures/moved_function.new.py
@@ -1,5 +1,5 @@
+def keep():
+    pass
+
 def calculate_total(x):
     return x
-
-def keep():
-    pass
```

The `MOVED` line is a review hint. The unified text diff below shows the exact edit. See the same input as a compact terminal comparison:

```bash
.venv/bin/linediff --display side-by-side --width 80 tests/fixtures/signature_body.old.py tests/fixtures/signature_body.new.py
```

The current fixture reports `+2 / -2 lines · 1 hunk` and shows old/new line numbers. Its 80-column view marks cropped lines with `…`; use the default unified view for full content.

To inspect a change in any local Git repository for one invocation, install Linediff there or put this environment's `linediff` on `PATH`, then run:

```bash
git -c diff.external=linediff diff --ext-diff
```

Use `linediff --diagnostics --display structural OLD NEW` to see whether Python AST analysis ran or a text fallback was used. Diagnostics go to stderr. The package's base installation needs no Tree-sitter grammar; optional grammar support is described in [parser support](PARSER_SUPPORT.md). [Input limits](LIMITS.md) and the [product contract](PRODUCT.md) state where the tool refuses or falls back.
