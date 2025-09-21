import subprocess
import tempfile
import os
import shutil
import pytest

DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(*args):
    cmd = DIFF_BINARY + list(args)
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    env['COVERAGE_PROCESS_START'] = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def test_file_comparison_basic():
    """Test basic file comparison."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("hello world\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("hello universe\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0  # Differences found but exit 0
        assert "world" in stdout
        assert "universe" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_check_only_mode():
    """Test --check-only mode."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("same\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("different\n")
        f2_path = f2.name

    try:
        # Without --check-only
        code1, _, _ = run_difft(f1_path, f2_path)
        # With --check-only
        code2, _, _ = run_difft('--check-only', f1_path, f2_path)
        assert code2 == 1  # Should exit with 1 when differences found
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_check_only_no_diff():
    """Test --check-only when no differences."""
    content = "identical\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write(content)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write(content)
        f2_path = f2.name

    try:
        code, _, _ = run_difft('--check-only', f1_path, f2_path)
        assert code == 0  # No differences
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_cli_help():
    """Test CLI help output."""
    code, stdout, stderr = run_difft('--help')
    assert code == 0

def test_display_modes():
    """Test different display modes."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("line 1\nline 2\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("line 1\nmodified line 2\n")
        f2_path = f2.name

    try:
        # Test unified (default)
        code1, stdout1, stderr1 = run_difft(f1_path, f2_path)
        assert code1 == 0
        assert "@@" in stdout1  # Should contain hunk markers

        # Test side-by-side
        code2, stdout2, stderr2 = run_difft('--display', 'side-by-side', f1_path, f2_path)
        assert code2 == 0
        assert "│" in stdout2  # Should contain side-by-side separator

        # Test inline
        code3, stdout3, stderr3 = run_difft('--display', 'inline', f1_path, f2_path)
        assert code3 == 0
        assert "line 2" in stdout3 and "modified line 2" in stdout3

    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)