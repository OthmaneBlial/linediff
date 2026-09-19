# Release preparation

No new release is implied by a green CI run or an Actions artifact. The tags through `v0.1.3` predate the current development code. Public PyPI and GitHub release publication require a separate maintainer decision and subsequent verification. The old `.env.example` requesting a PyPI token was removed because the candidate script does not read credentials or upload anything.

## Prepare a candidate

1. Finish the release gates in [ROADMAP.md](../ROADMAP.md). Choose an unused PEP 440 version; update `pyproject.toml`, move the verified Unreleased changes into a dated section of `CHANGELOG.md`, and review the release notes.
2. Commit those edits and all intended code. Confirm `git status --short` is empty. The build script refuses a dirty tree or an existing `vVERSION` tag.
3. Run `PYTHON=/path/to/venv/bin/python bash scripts/release-kit.sh --dry-run`. The dry run reads metadata and Git state only. It does not install tools, build, tag, push or upload.
4. Run `PYTHON=/path/to/venv/bin/python bash scripts/release-kit.sh --build --out-dir /tmp/linediff-candidate-VERSION`. The output directory must be empty. The script runs tests, Ruff, local link checks, wheel/sdist build, `twine check`, isolated installation smoke tests and SHA-256 output. It never reads credentials or publishes.
5. Optionally dispatch the read-only [Release candidate workflow](../.github/workflows/release-candidate.yml) for the committed version. It builds wheel/sdist, installs the downloaded archives on three OSes at Python 3.8 and 3.14, then builds OS-specific standalone archives. These are temporary GitHub Actions artifacts, not a GitHub Release or PyPI files. Inspect every job, download the artifacts, verify checksums and smoke-test the download outside the checkout.

The current source version is `0.2.0a1`, with a dated candidate section in the changelog and no corresponding tag. The candidate preflight can now check this version. The existing `scripts/release-kit.sh` upload path was removed because it could mutate and publish before validation.

## Publication gate

Before any public publication, review the exact commit, version, notes, artifact hashes, supported platform claims, workflow permissions and target accounts. Use an explicitly approved publication path with short-lived identity where available. Then verify the remote GitHub Release and PyPI page separately, download their artifacts, compare hashes, install from the downloaded files and run the product smoke scenarios. Record the result and only then add public release links to the README. No publication workflow or credential is configured in this repository yet.
