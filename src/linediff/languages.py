"""CLI language names; only a subset has a verified structural view."""

from pathlib import Path


EXTENSIONS = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".txt": "text",
}

KNOWN_LANGUAGES = frozenset(EXTENSIONS.values()) | {"text"}


def detect_language(file_path: str) -> str:
    """Name a file for CLI routing; naming does not imply structural support."""
    return EXTENSIONS.get(Path(file_path).suffix.lower(), "text")
