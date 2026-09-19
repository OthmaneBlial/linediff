"""Build and smoke-test a base CLI executable for the current OS/architecture."""

import argparse
import hashlib
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(*arguments):
    subprocess.run(list(arguments), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--label", required=True, help="Version or explicit dev label")
    args = parser.parse_args()
    if not args.label.replace("-", "").replace(".", "").isalnum():
        parser.error("label may contain only letters, digits, dots and hyphens")

    os_name = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(
        platform.system()
    )
    if os_name is None:
        parser.error("unsupported build host")
    arch = platform.machine().lower()
    arch = {"amd64": "x86_64", "aarch64": "arm64"}.get(arch, arch)
    executable_name = "linediff.exe" if os.name == "nt" else "linediff"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if any(args.out_dir.iterdir()):
        parser.error("output directory must be empty")
    output = args.out_dir.resolve()

    with tempfile.TemporaryDirectory(prefix="linediff-freeze-") as temporary:
        work = Path(temporary)
        run(
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--console",
            "--name",
            "linediff",
            "--paths",
            str(ROOT / "src"),
            "--distpath",
            str(work / "dist"),
            "--workpath",
            str(work / "build"),
            "--specpath",
            str(work / "spec"),
            str(ROOT / "scripts" / "linediff_entry.py"),
        )
        executable = work / "dist" / executable_name
        run(
            sys.executable,
            str(ROOT / "scripts" / "smoke_standalone.py"),
            str(executable),
        )

        base = "linediff-{}-{}-{}".format(args.label, os_name, arch)
        archive = output / (base + (".zip" if os_name == "windows" else ".tar.gz"))
        if os_name == "windows":
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                bundle.write(executable, executable_name)
                bundle.write(ROOT / "LICENSE", "LICENSE")
        else:
            with tarfile.open(archive, "w:gz") as bundle:
                bundle.add(executable, arcname=executable_name)
                bundle.add(ROOT / "LICENSE", arcname="LICENSE")
        extract_dir = work / "unpacked"
        extract_dir.mkdir()
        if os_name == "windows":
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extract_dir)
        else:
            with tarfile.open(archive, "r:gz") as bundle:
                bundle.extractall(extract_dir, filter="data")
        run(
            sys.executable,
            str(ROOT / "scripts" / "smoke_standalone.py"),
            str(extract_dir / executable_name),
        )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (output / (archive.name + ".sha256")).write_text(
            "{}  {}\n".format(digest, archive.name), encoding="ascii"
        )
        print(
            "PASS {} ({} bytes; SHA-256 {})".format(
                archive.name, archive.stat().st_size, digest
            )
        )


if __name__ == "__main__":
    main()
