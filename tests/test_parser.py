import subprocess
import os
import tempfile
import pytest

DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(file1, file2, *args):
    cmd = DIFF_BINARY + list(args) + [file1, file2]
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def test_tree_sitter_integration_javascript():
    """Test parsing with JavaScript files."""
    content1 = "function foo() { return 1; }"
    content2 = "function bar() { return 2; }"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert len(stdout) > 0
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_tree_sitter_integration_python():
    """Test parsing with Python files."""
    content1 = "def foo():\n    return 1"
    content2 = "def bar():\n    return 2"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert len(stdout) > 0
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_tree_sitter_integration_json():
    """Test parsing with JSON files."""
    content1 = '{"key": "value1"}'
    content2 = '{"key": "value2"}'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should produce output
        assert len(stdout) > 0
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_fallback_parsing():
    """Test parsing with malformed files."""
    content1 = "function foo() { return 1; "  # Missing closing brace
    content2 = "function bar() { return 2; }"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        # Should still produce output even with syntax errors
        assert code == 0 or code == 1  # 1 might indicate differences
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)
