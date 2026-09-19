#!/usr/bin/env python3
"""Fail when a repository Markdown link points to a missing file or heading."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "CHANGELOG.md")]
DOCUMENTS += sorted((ROOT / "docs").glob("*.md"))
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)


def headings(path):
    found = set()
    for title in HEADING.findall(path.read_text(encoding="utf-8")):
        title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", title)
        title = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        found.add(title)
    return found


def main():
    errors = []
    for document in DOCUMENTS:
        for raw in LINK.findall(document.read_text(encoding="utf-8")):
            if raw.startswith(("http:", "https:", "mailto:", "data:")):
                continue
            target_name, _, fragment = unquote(raw).partition("#")
            target = (
                (document.parent / target_name).resolve() if target_name else document
            )
            if not target.is_file():
                errors.append("{}: missing {}".format(document.relative_to(ROOT), raw))
            elif (
                fragment
                and target.suffix.lower() == ".md"
                and fragment not in headings(target)
            ):
                errors.append(
                    "{}: missing heading {}".format(document.relative_to(ROOT), raw)
                )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Checked {} Markdown files: local links resolve".format(len(DOCUMENTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
