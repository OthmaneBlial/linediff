# Security policy

The maintained development branch is `main`. The older `v0.1.3` tag predates current input guards; no new public release has been verified. Check the [roadmap](ROADMAP.md) and [releases page](https://github.com/OthmaneBlial/linediff/releases) before relying on a packaged fix.

Please do not disclose a suspected vulnerability in a public issue. Send a private report to the maintainer address listed in `pyproject.toml` with a minimal non-sensitive reproducer, affected commit or version, platform, and likely impact. Do not send credentials or private source files. We will investigate and coordinate a fix and disclosure; no response-time guarantee is claimed here.

Linediff reads user-chosen files as data. It does not execute compared source code. The CLI rejects terminal control and bidi override characters in ordinary text and paths; Git external mode reports unsafe text without rendering it. See [input limits](docs/LIMITS.md) for current resource guards. Git integration invokes Linediff through Git's external-diff protocol; the tool itself does not change Git configuration.
