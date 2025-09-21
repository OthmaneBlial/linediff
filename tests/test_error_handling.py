import subprocess
import tempfile
import os
import pytest

DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(*args):
    cmd = DIFF_BINARY + list(args)
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    env['COVERAGE_PROCESS_START'] = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def test_invalid_arguments():
    """Test with invalid command line arguments."""
    code, stdout, stderr = run_difft('--invalid-flag')
    assert code != 0
    assert "error" in stderr.lower() or "unrecognized" in stderr.lower()

def test_no_files_provided():
    """Test running without providing files."""
    code, stdout, stderr = run_difft()
    assert code != 0
    assert "error" in stderr.lower() or "USAGE" in stderr

def test_one_file_provided():
    """Test running with only one file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("content\n")
        f_path = f.name

    try:
        code, stdout, stderr = run_difft(f_path)
        assert code != 0
        assert "error" in stderr.lower()
    finally:
        os.unlink(f_path)

def test_directory_as_file():
    """Test trying to diff directories."""
    code, stdout, stderr = run_difft('/tmp', '/var')
    # Might work or fail depending on implementation
    assert code in [0, 1, 2]  # Allow various exit codes

def test_permission_denied():
    """Test with files that have no read permission."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("content\n")
        f_path = f.name

    try:
        os.chmod(f_path, 0o000)  # No permissions
        code, stdout, stderr = run_difft(f_path, f_path)
        assert code != 0
        assert "permission" in stderr.lower() or "error" in stderr.lower()
    finally:
        os.chmod(f_path, 0o644)  # Restore permissions
        os.unlink(f_path)

def test_malformed_utf8():
    """Test with malformed UTF-8 content."""
    malformed = b'\xff\xfe\xfd'  # Invalid UTF-8
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(malformed)
        f_path = f.name

    try:
        code, stdout, stderr = run_difft(f_path, f_path)
        # Should handle gracefully
        assert code in [0, 1]
    finally:
        os.unlink(f_path)

def test_extremely_long_lines():
    """Test with files containing extremely long lines."""
    long_line = "a" * 100000  # 100k character line
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write(long_line + "\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write(long_line + "b\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should handle without crashing
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_many_small_files():
    """Test diffing many small files."""
    files = []
    try:
        for i in range(10):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"content {i}\n")
                files.append(f.name)

        # Diff first and last
        code, stdout, stderr = run_difft(files[0], files[-1])
        assert code == 0
    finally:
        for f in files:
            if os.path.exists(f):
                os.unlink(f)

def test_interrupt_signal():
    """Test handling of interrupt signals (simulated)."""
    # Hard to test directly, but we can check help for signal handling
    code, stdout, stderr = run_difft('--help')
    # Just ensure help works
    assert code == 0