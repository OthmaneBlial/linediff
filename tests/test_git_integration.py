"""Exercise the actual seven-argument protocol used by Git external diff."""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("git"), "git is required")
class GitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Linediff test")
        self.git("config", "user.email", "test@example.invalid")
        files = {
            "changed.py": b"before\n",
            "deleted.py": b"deleted\n",
            "renamed.py": b"renamed\n",
            "rename-only.py": b"same content\n",
            "binary.dat": b"\x00\x01",
            "space name.py": b"before space\n",
        }
        for name, content in files.items():
            (self.repository / name).write_bytes(content)
        self.git("add", ".")
        self.git("commit", "-qm", "base")

        (self.repository / "changed.py").write_bytes(b"after\n")
        (self.repository / "deleted.py").unlink()
        self.git("mv", "renamed.py", "renamed-again.py")
        self.git("mv", "rename-only.py", "rename-only-new.py")
        (self.repository / "renamed-again.py").write_bytes(b"renamed\nupdated\n")
        (self.repository / "binary.dat").write_bytes(b"\x00\x02")
        (self.repository / "space name.py").write_bytes(b"after space\n")
        (self.repository / "added.py").write_bytes(b"added\n")
        self.git("add", "-A")

    def git(self, *arguments, env=None):
        return subprocess.run(
            ["git"] + list(arguments),
            cwd=self.repository,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

    def test_one_shot_external_diff_handles_common_git_changes(self):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        command = shlex.quote(sys.executable) + " -m linediff"
        result = self.git(
            "-c", "diff.external=" + command, "diff", "--cached", "--ext-diff", env=env
        )
        output = result.stdout
        self.assertIn("--- /dev/null\n+++ b/added.py", output)
        self.assertIn("--- a/deleted.py\n+++ /dev/null", output)
        self.assertIn("--- a/changed.py\n+++ b/changed.py", output)
        self.assertIn("-before\n+after", output.replace("\r\n", "\n"))
        self.assertIn("Binary files differ: binary.dat", output)
        self.assertIn("space name.py", output)
        self.assertIn("--- a/renamed.py\n+++ b/renamed-again.py", output)
        self.assertIn("Renamed: rename-only.py -> rename-only-new.py", output)

        native = self.git("diff", "--cached", "--no-ext-diff")
        self.assertIn("diff --git a/changed.py b/changed.py", native.stdout)
        local_setting = subprocess.run(
            ["git", "config", "--local", "--get", "diff.external"],
            cwd=self.repository,
            capture_output=True,
        )
        self.assertEqual(local_setting.returncode, 1)

    def test_seven_arguments_are_not_confused_with_two_file_mode(self):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        old = self.repository / "binary.dat"
        new = self.repository / "added.py"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linediff",
                "sample.dat",
                str(old),
                "oldhex",
                "100644",
                str(new),
                "newhex",
                "100644",
            ],
            cwd=self.repository,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Binary files differ: sample.dat")

    def test_identical_git_objects_are_rename_even_with_checkout_line_endings(self):
        old = self.repository / "old-view.py"
        new = self.repository / "new-view.py"
        old.write_bytes(b"same\n")
        new.write_bytes(b"same\r\n")
        sha = "a" * 40
        arguments = [
            sys.executable,
            "-m",
            "linediff",
            "old-view.py",
            str(old),
            sha,
            "100644",
            str(new),
            sha,
            "100644",
            "new-view.py",
            sha,
        ]
        display = subprocess.run(
            arguments,
            cwd=self.repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(display.returncode, 0, display.stderr)
        self.assertEqual(display.stdout.strip(), "Renamed: old-view.py -> new-view.py")
        check = subprocess.run(
            arguments[:3] + ["--check-only"] + arguments[3:],
            cwd=self.repository,
            capture_output=True,
        )
        self.assertEqual(check.returncode, 1)
        self.assertEqual(check.stdout, b"")

    def test_git_unsafe_text_uses_status_without_terminal_control(self):
        old = self.repository / "unsafe-old.txt"
        new = self.repository / "unsafe-new.txt"
        old.write_bytes(b"before\n")
        new.write_bytes(b"after\x1b[2J\n")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "linediff",
                "sample.txt",
                str(old),
                "oldhex",
                "100644",
                str(new),
                "newhex",
                "100644",
            ],
            cwd=self.repository,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout.strip(), b"Terminal-unsafe text differs: sample.txt"
        )
        self.assertNotIn(b"\x1b", result.stdout)

        old.write_bytes(new.read_bytes())
        identical = subprocess.run(
            [
                sys.executable,
                "-m",
                "linediff",
                "sample.txt",
                str(old),
                "oldhex",
                "100644",
                str(new),
                "newhex",
                "100644",
            ],
            cwd=self.repository,
            capture_output=True,
        )
        self.assertEqual(identical.returncode, 0)
        self.assertEqual(identical.stdout, b"")

        bad_mode = subprocess.run(
            [
                sys.executable,
                "-m",
                "linediff",
                "sample.txt",
                str(old),
                "oldhex",
                "100644\x1b[2J",
                str(new),
                "newhex",
                "100644",
            ],
            cwd=self.repository,
            capture_output=True,
        )
        self.assertEqual(bad_mode.returncode, 2)
        self.assertEqual(bad_mode.stdout, b"")
        self.assertNotIn(b"\x1b", bad_mode.stderr)


if __name__ == "__main__":
    unittest.main()
