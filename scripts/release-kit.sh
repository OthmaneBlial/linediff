#!/usr/bin/env bash
# Validate and build a release candidate. Publication is a separate, approved step.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
    cat <<'EOF'
Usage: scripts/release-kit.sh [--dry-run | --build --out-dir DIRECTORY]

The package version and dated changelog entry must already be committed.
--dry-run checks release metadata and the Git tree without changing files.
--build runs local gates, builds wheel/sdist, checks them, and smoke-tests both.
This script never tags, pushes, uploads, publishes, or reads credentials.
EOF
}

mode=dry-run
out_dir=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            [[ "$mode" == dry-run && -z "$out_dir" ]] || { usage >&2; exit 2; }
            shift
            ;;
        --build)
            [[ "$mode" == dry-run ]] || { usage >&2; exit 2; }
            mode=build
            shift
            ;;
        --out-dir)
            [[ $# -ge 2 && -z "$out_dir" ]] || { usage >&2; exit 2; }
            out_dir="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

[[ "$mode" == build && -n "$out_dir" || "$mode" == dry-run && -z "$out_dir" ]] || {
    usage >&2
    exit 2
}

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Release candidate requires a clean Git tree" >&2
    exit 1
fi

python_bin="${PYTHON:-python3}"
version=$("$python_bin" - <<'PY'
from pathlib import Path
import re

project = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'(?m)^version = "([^"]+)"$', project)
if not match or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:a[0-9]+|b[0-9]+|rc[0-9]+)?", match.group(1)):
    raise SystemExit("Expected one explicit PEP 440 release version in pyproject.toml")
version = match.group(1)
changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
if not re.search(r"(?m)^## \[{}\] - \d{{4}}-\d{{2}}-\d{{2}}$".format(re.escape(version)), changelog):
    raise SystemExit("Add a dated changelog section for {} before building".format(version))
print(version)
PY
)

if git rev-parse --verify --quiet "refs/tags/v${version}" >/dev/null; then
    echo "Tag v${version} already exists; choose an unused version" >&2
    exit 1
fi

printf 'Release candidate: v%s at %s\n' "$version" "$(git rev-parse --short HEAD)"
if [[ "$mode" == dry-run ]]; then
    echo "Dry run passed. Build will run tests, Ruff, link check, build, twine check and wheel/sdist smoke tests."
    exit 0
fi

"$python_bin" -m pytest -q
"$python_bin" -m ruff check src/linediff tests scripts
"$python_bin" -m ruff format --check src/linediff tests scripts
"$python_bin" scripts/check_docs.py

mkdir -p "$out_dir"
out_dir="$(cd "$out_dir" && pwd)"
if [[ -n "$(find "$out_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "Output directory must be empty: $out_dir" >&2
    exit 1
fi

"$python_bin" -m build --outdir "$out_dir"
"$python_bin" -m twine check "$out_dir"/*
"$python_bin" scripts/smoke_dist.py "$out_dir"
"$python_bin" - "$out_dir" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys

for artifact in sorted(Path(sys.argv[1]).iterdir()):
    print("{}  {}".format(sha256(artifact.read_bytes()).hexdigest(), artifact))
PY
