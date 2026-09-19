import subprocess
import sys
import os
import tempfile

DIFF_BINARY = [sys.executable, "-m", "linediff"]


def run_difft(file1, file2, *args):
    cmd = DIFF_BINARY + list(args) + [file1, file2]
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr


def test_javascript_uses_exact_text_diff():
    """The CLI does not imply structural JavaScript support."""
    content1 = "function foo() { return 1; }"
    content2 = "function bar() { return 2; }"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert "-function foo() { return 1; }" in stdout
        assert "+function bar() { return 2; }" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)


def test_python_default_uses_exact_text_diff():
    """The default route remains an applicable text diff."""
    content1 = "def foo():\n    return 1"
    content2 = "def bar():\n    return 2"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert "-def foo():" in stdout
        assert "+def bar():" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)


def test_json_uses_exact_text_diff():
    """Installed grammars do not silently change the CLI route."""
    content1 = '{"key": "value1"}'
    content2 = '{"key": "value2"}'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert '-{"key": "value1"}' in stdout
        assert '+{"key": "value2"}' in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)


def test_malformed_javascript_still_has_text_diff():
    """Malformed JavaScript is compared as text."""
    content1 = "function foo() { return 1; "  # Missing closing brace
    content2 = "function bar() { return 2; }"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        assert "-function foo() { return 1; " in stdout
        assert "+function bar() { return 2; }" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)
