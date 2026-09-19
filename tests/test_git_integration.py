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
            check=True,
        )

    def test_one_shot_external_diff_handles_common_git_changes(self):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        command = shlex.quote(sys.executable) + " -m linediff"
        result = self.git("-c", "diff.external=" + command, "diff", "--cached", "--ext-diff", env=env)
        output = result.stdout
        self.assertIn("--- /dev/null\n+++ b/added.py", output)
        self.assertIn("--- a/deleted.py\n+++ /dev/null", output)
        self.assertIn("--- a/changed.py\n+++ b/changed.py", output)
        self.assertIn("-before\n+after", output)
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
            [sys.executable, "-m", "linediff", "sample.dat", str(old), "oldhex", "100644", str(new), "newhex", "100644"],
            cwd=self.repository,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Binary files differ: sample.dat")


if __name__ == "__main__":
    unittest.main()
