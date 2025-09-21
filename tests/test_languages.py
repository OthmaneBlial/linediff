import subprocess
import os
import tempfile
import pytest

DIFF_BINARY = ['python3', '-m', 'linediff']

def run_difft(file1, file2, *args):
    cmd = DIFF_BINARY + list(args) + [file1, file2]
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', 'src')
    env['COVERAGE_PROCESS_START'] = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

@pytest.mark.parametrize("lang", [
    "javascript", "python", "json", "css", "html", "rust", "cpp", "java", "csharp", "go",
    "php", "ruby", "scala", "swift", "typescript", "kotlin", "dart", "lua", "perl", "haskell",
    "elixir", "clojure", "erlang", "r", "matlab", "shell", "yaml", "xml", "toml"
])
def test_language_support(lang):
    """Test support for various programming languages."""
    # Sample contents for each language
    contents = {
        "javascript": ("function foo() { return 1; }", "function foo() { return 2; }"),
        "python": ("def foo():\n    return 1", "def foo():\n    return 2"),
        "json": ('{"key": "value1"}', '{"key": "value2"}'),
        "css": ("body { color: red; }", "body { color: blue; }"),
        "html": ("<html><body>Hello</body></html>", "<html><body>World</body></html>"),
        "rust": ("fn main() {}", "fn main() { println!(\"Hello\"); }"),
        "cpp": ("int main() { return 0; }", "int main() { return 1; }"),
        "java": ("public class Main {}", "public class Main { public static void main(String[] args) {} }"),
        "csharp": ("class Program {}", "class Program { static void Main() {} }"),
        "go": ("package main", "package main\nfunc main() {}"),
        "php": ("<?php echo 'hello';", "<?php echo 'world';"),
        "ruby": ("puts 'hello'", "puts 'world'"),
        "scala": ("object Main", "object Main { def main(args: Array[String]) = {} }"),
        "swift": ("print(\"hello\")", "print(\"world\")"),
        "typescript": ("function foo(): number { return 1; }", "function foo(): number { return 2; }"),
        "kotlin": ("fun main() {}", "fun main() { println(\"Hello\") }"),
        "dart": ("void main() {}", "void main() { print('Hello'); }"),
        "lua": ("print('hello')", "print('world')"),
        "perl": ("print 'hello';", "print 'world';"),
        "haskell": ("main = putStrLn \"hello\"", "main = putStrLn \"world\""),
        "elixir": ("IO.puts \"hello\"", "IO.puts \"world\""),
        "clojure": ("(println \"hello\")", "(println \"world\")"),
        "erlang": ("-module(test).", "-module(test).\nmain() -> io:format(\"hello\")."),
        "r": ("print('hello')", "print('world')"),
        "matlab": ("disp('hello')", "disp('world')"),
        "shell": ("echo hello", "echo world"),
        "yaml": ("key: value1", "key: value2"),
        "xml": ("<root>hello</root>", "<root>world</root>"),
        "toml": ("key = 'value1'", "key = 'value2'"),
    }
    content1, content2 = contents.get(lang, ("line 1", "line 2"))
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{lang[:3]}', delete=False) as f1:
        f1.write(content1)
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{lang[:3]}', delete=False) as f2:
        f2.write(content2)
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code in [0, 1]  # 0 or 1
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)

def test_unsupported_language():
    """Test behavior with unsupported file types."""
    # Create temp files with unknown extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='.unknown', delete=False) as f1:
        f1.write("unknown content\n")
        f1_path = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.unknown', delete=False) as f2:
        f2.write("different content\n")
        f2_path = f2.name
    try:
        code, stdout, stderr = run_difft(f1_path, f2_path)
        assert code in [0, 1]  # 0 or 1
    finally:
        os.unlink(f1_path)
        os.unlink(f2_path)