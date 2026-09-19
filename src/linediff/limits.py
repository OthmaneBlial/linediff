"""Conservative input budgets for exact and structural comparison."""

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_LINES = 20_000
MAX_LINE_CHARS = 200_000
MAX_STRUCTURAL_BYTES = 1 * 1024 * 1024
MAX_DEFINITIONS = 500


class DiffLimitError(ValueError):
    """Comparison would exceed a documented resource budget."""


def validate_text(content: str, label: str) -> None:
    if len(content.encode('utf-8')) > MAX_INPUT_BYTES:
        raise DiffLimitError("{} exceeds the 4 MiB UTF-8 input limit".format(label))
    lines = content.splitlines(keepends=True)
    if len(lines) > MAX_LINES:
        raise DiffLimitError("{} exceeds the 20,000-line input limit".format(label))
    if any(len(line) > MAX_LINE_CHARS for line in lines):
        raise DiffLimitError("{} has a line longer than 200,000 characters".format(label))
