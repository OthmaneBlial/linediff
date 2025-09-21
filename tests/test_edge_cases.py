import subprocess
import tempfile
import os
import pytest

DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(file1, file2, *args):
    cmd = DIFF_BINARY + list(args) + [file1, file2]
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    env['COVERAGE_PROCESS_START'] = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def test_empty_files():
    """Test diffing empty files."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1_path = f1.name  # Empty
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2_path = f2.name  # Empty

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0  # No differences
        # linediff outputs header even for identical files
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_one_empty_one_not():
    """Test diffing one empty and one non-empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1_path = f1.name  # Empty
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("content\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        assert "content" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_large_files():
    """Test diffing large files."""
    large_content = "line\n" * 10000  # 50k lines
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write(large_content)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write(large_content + "extra\n")
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        # Should handle large files without crashing
        assert "extra" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_binary_content():
    """Test diffing binary files."""
    binary_content1 = b'\x00\x01\x02\x03hello\x04\x05'
    binary_content2 = b'\x00\x01\x02\x03world\x04\x05'
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f1:
        f1.write(binary_content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f2:
        f2.write(binary_content2)
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        # Binary files might be handled differently
        assert code in [0, 1]
        # Should not crash
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_unicode_content():
    """Test diffing files with unicode content."""
    unicode_content1 = "héllo wörld 🌍\n"
    unicode_content2 = "héllo universe 🌍\n"
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f1:
        f1.write(unicode_content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f2:
        f2.write(unicode_content2)
        f2_path = f2.name

    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code == 0
        assert "wörld" in stdout or "universe" in stdout
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_nonexistent_file():
    """Test behavior with nonexistent files."""
    code, stdout, stderr = run_difft('/nonexistent1', '/nonexistent2')
    assert code != 0  # Should fail
    assert "error" in stderr.lower()

def test_same_file():
    """Test diffing the same file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("content\n")
        f_path = f.name

    try:
        code, stdout, stderr = run_difft(f_path, f_path)
        assert code == 0
        # linediff outputs header even for identical files
    finally:
        os.unlink(f_path)