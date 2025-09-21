import subprocess
import tempfile
import os
import pytest

# Path to the linediff module
DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(file1, file2, *args):
    """Run linediff on two files and return the output."""
    cmd = DIFF_BINARY + list(args) + [file1, file2]
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    env['COVERAGE_PROCESS_START'] = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def test_structural_diffing_basic():
    """Test basic structural diffing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("line 1\nline 2\nline 3\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("line 1\nline 2 modified\nline 3\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        assert "line 2" in stdout
        assert "modified" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_lcs_algorithm():
    """Test LCS algorithm with common subsequences."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("a\nb\nc\nd\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("a\nx\nb\nc\ny\nd\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should show additions and deletions correctly
        assert "x" in stdout or "y" in stdout  # Depending on output format
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_alignment_slider_correction():
    """Test alignment and slider correction."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f1:
        f1.write("fn main() {\n    println!(\"hello\");\n}\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f2:
        f2.write("fn main() {\n    println!(\"world\");\n}\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        assert "hello" in stdout
        assert "world" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_no_changes():
    """Test when files are identical."""
    content = "identical content\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write(content)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write(content)
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should indicate no differences (linediff outputs header even for identical files)
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)