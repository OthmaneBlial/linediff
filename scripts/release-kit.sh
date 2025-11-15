#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYPROJECT="$REPO_ROOT/pyproject.toml"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"
TAG_PREFIX="v"
REMOTE="origin"

BUMP_TYPE=""
NEW_VERSION=""
RELEASE_NOTES=""
NOTES_FILE=""
REPO="pypi"
DRY_RUN=false
SKIP_TESTS=false
SKIP_CHECK=false
SKIP_UPLOAD=false
SKIP_GIT=false
SKIP_PUSH=false

log() {
    printf "➤ %s\n" "$*"
}

die() {
    printf "❌ %s\n" "$*" >&2
    exit 1
}

require_command() {
    if ! command -v "$1" &> /dev/null; then
        die "required command '$1' is missing"
    fi
}

load_env_file() {
    local env_file="$REPO_ROOT/.env"
    if [[ -f "$env_file" ]]; then
        log "Loading credentials from .env"
        set -o allexport
        # shellcheck source=/dev/null
        source "$env_file"
        set +o allexport
    fi
}

run_or_dry() {
    log "$*"
    if [[ "$DRY_RUN" == "false" ]]; then
        "$@"
    else
        log "(dry-run; skipping execution)"
    fi
}

prompt() {
    local prompt="$1"
    local default="$2"
    local answer
    read -rp "$prompt" answer
    if [[ -z "$answer" ]]; then
        printf '%s\n' "$default"
    else
        printf '%s\n' "$answer"
    fi
}

usage() {
    cat <<'EOF'
Usage: $(basename "$0") [options]

Options:
  -b, --bump TYPE         semver bump (patch/minor/major); prompted if omitted
  -v, --version VERSION   set explicit version instead of bumping
  -n, --notes TEXT        release notes (can include Markdown)
  --notes-file PATH       load release notes from a file
  -r, --repo NAME         twine repository (default: pypi)
  --dry-run               show actions without executing them
  --skip-tests            skip pytest
  --skip-check            skip `twine check`
  --skip-upload           build but do not upload
  --no-git                skip git checks, commits, and tags
  --no-push               skip pushing commits and tags
  -h, --help              display this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -b|--bump)
            BUMP_TYPE="$2"
            shift 2
            ;;
        -v|--version)
            NEW_VERSION="$2"
            shift 2
            ;;
        -n|--notes)
            RELEASE_NOTES="$2"
            shift 2
            ;;
        --notes-file)
            NOTES_FILE="$2"
            shift 2
            ;;
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-check)
            SKIP_CHECK=true
            shift
            ;;
        --skip-upload)
            SKIP_UPLOAD=true
            shift
            ;;
        --no-git)
            SKIP_GIT=true
            shift
            ;;
        --no-push)
            SKIP_PUSH=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unexpected argument: $1"
            ;;
    esac
done

cd "$REPO_ROOT"

load_env_file

require_command python
require_command git
require_command rm
require_command pip

log "Starting release conductor"

log "Ensuring build tooling"
needs_install=false
if ! command -v twine &> /dev/null; then
    needs_install=true
    log "Twine missing"
fi

if ! python - <<'PY'
import importlib, sys

try:
    importlib.import_module("build")
except ImportError:
    sys.exit(1)
PY
then
    needs_install=true
    log "Build module missing"
fi

if [[ "$needs_install" == "true" ]]; then
    run_or_dry python -m pip install --upgrade --quiet build twine
else
    log "Build tooling already installed"
fi

current_version=$(
    PYPROJECT_PATH="$PYPROJECT" python - <<'PY'
from pathlib import Path
import os, re, sys

path = Path(os.environ["PYPROJECT_PATH"])
text = path.read_text()
match = re.search(r'^\s*version\s*=\s*(["\'])([^"\']+)\1', text, re.MULTILINE)
if not match:
    print(f"version not declared in {path}", file=sys.stderr)
    sys.exit(1)
print(match.group(2))
PY
)

log "Current version: $current_version"

if [[ -n "$NOTES_FILE" ]]; then
    if [[ ! -f "$NOTES_FILE" ]]; then
        die "notes file '$NOTES_FILE' does not exist"
    fi
    RELEASE_NOTES=$(< "$NOTES_FILE")
fi

if [[ -z "$NEW_VERSION" ]]; then
    if [[ -z "$BUMP_TYPE" ]]; then
        echo "Choose version bump (patch/minor/major). Default: patch"
        BUMP_TYPE=$(prompt "Bump type: [patch] " "patch")
    fi
    case "$BUMP_TYPE" in
        patch|minor|major) ;;
        *)
            die "invalid bump type '$BUMP_TYPE'; choose patch, minor or major"
            ;;
    esac
    NEW_VERSION=$(
        CURRENT_VERSION="$current_version" BUMP_TYPE="$BUMP_TYPE" python - <<'PY'
import os, sys

current = os.environ["CURRENT_VERSION"].split(".")
if len(current) < 3:
    raise SystemExit("expected semver-like version in pyproject.toml")
major, minor, patch = map(int, current[:3])
bump = os.environ["BUMP_TYPE"]
if bump == "patch":
    patch += 1
elif bump == "minor":
    minor += 1
    patch = 0
elif bump == "major":
    major += 1
    minor = 0
    patch = 0
print(f"{major}.{minor}.{patch}")
PY
    )
fi

log "New version: $NEW_VERSION"

if [[ -z "$RELEASE_NOTES" ]]; then
    RELEASE_NOTES="- TODO: describe the changes for $NEW_VERSION"
fi

today=$(date -u +"%Y-%m-%d")

if [[ ! -f "$CHANGELOG" ]]; then
    cat <<'HEADER' > "$CHANGELOG"
# Changelog
All notable changes to this project will be documented here.

HEADER
fi

existing_entries=$(tail -n +4 "$CHANGELOG" || true)

{
    printf '# Changelog\nAll notable changes to this project will be documented here.\n\n'
    printf '## [%s] - %s\n\n%s\n\n' "$NEW_VERSION" "$today" "$RELEASE_NOTES"
    if [[ -n "$existing_entries" ]]; then
        printf '%s\n' "$existing_entries"
    fi
} > "$CHANGELOG"

NEW_VERSION="$NEW_VERSION" python - <<'PY'
from pathlib import Path
import os, re

path = Path("pyproject.toml")
new_version = os.environ["NEW_VERSION"]
data = path.read_text()
new = re.sub(r'(?m)^version\s*=\s*".*"$', f'version = "{new_version}"', data, count=1)
if data == new:
    raise SystemExit("failed to update version in pyproject")
path.write_text(new)
PY

log "Updated pyproject.toml + CHANGELOG.md"

if [[ "$SKIP_GIT" != "true" ]]; then
    if [[ -n $(git status --porcelain) ]]; then
        die "git working tree is dirty; stash/commit before releasing"
    fi
    branch=$(git symbolic-ref --short HEAD)
    log "on branch $branch"
fi

if [[ "$SKIP_TESTS" != "true" ]]; then
    run_or_dry python -m pytest --color=yes -v --tb=short
else
    log "Skipping pytest (--skip-tests)"
fi

log "Cleaning previous build artifacts"
if [[ "$DRY_RUN" == "false" ]]; then
    rm -rf build dist *.egg-info
else
    log "(dry-run; skipping rm -rf build dist *.egg-info)"
fi

run_or_dry python -m build

if [[ "$SKIP_CHECK" != "true" ]]; then
    run_or_dry twine check dist/*
else
    log "Skipping twine check (--skip-check)"
fi

if [[ "$SKIP_UPLOAD" == "true" ]]; then
    log "Upload skipped (--skip-upload)"
else
    placeholder="pypi-XXXXXXXXXXXXXXXXXXXXXXXX"
    detect_placeholder() {
        local value="$1"
        if [[ "$value" == *"$placeholder"* ]]; then
            die "placeholder PyPI token detected; configure a real API token"
        fi
    }

    if [[ -z "${TWINE_USERNAME:-}" ]] || [[ -z "${TWINE_PASSWORD:-}" ]]; then
        config_file=""
        if [[ -f "$REPO_ROOT/.pypirc" ]]; then
            config_file="$REPO_ROOT/.pypirc"
        elif [[ -f "$HOME/.pypirc" ]]; then
            config_file="$HOME/.pypirc"
        fi
        if [[ -z "$config_file" ]]; then
            die "no PyPI credentials found; set TWINE_USERNAME/TWINE_PASSWORD or create ~/.pypirc"
        fi
        detect_placeholder "$(cat "$config_file")"
    else
        detect_placeholder "$TWINE_PASSWORD"
    fi

    run_or_dry twine upload --repository "$REPO" dist/*
fi

if [[ "$SKIP_GIT" != "true" ]]; then
    run_or_dry git add pyproject.toml CHANGELOG.md
    commit_message="chore: release $NEW_VERSION"
    run_or_dry git commit -m "$commit_message"
    tag_name="$TAG_PREFIX$NEW_VERSION"
    run_or_dry git tag -a "$tag_name" -m "Release $NEW_VERSION"

    if [[ "$SKIP_PUSH" == "true" ]]; then
        log "Push suppressed (--no-push)"
    else
        run_or_dry git push "$REMOTE" "$branch"
        run_or_dry git push "$REMOTE" "$tag_name"
    fi
else
    log "Git operations skipped (--no-git)"
fi

log "Release $NEW_VERSION complete"
