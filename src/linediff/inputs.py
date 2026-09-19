"""Read user-supplied file and stdin operands without changing their bytes."""

import re
import sys
from pathlib import Path
from typing import Tuple


class LinediffInputError(Exception):
    """An input cannot be compared as UTF-8 text."""


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as stream:
            content = stream.read()
    except UnicodeDecodeError as error:
        raise LinediffInputError("Cannot decode '{}' as UTF-8".format(file_path)) from error
    except OSError as error:
        raise LinediffInputError(
            "Cannot read '{}': {}".format(file_path, error.strerror or error)
        ) from error
    if '\x00' in content:
        raise LinediffInputError("Binary file '{}' contains NUL bytes".format(file_path))
    return content


def read_git_bytes(file_path: str) -> bytes:
    """Read a Git external-diff operand, including its null-file sentinel."""
    if file_path == '/dev/null':
        return b''
    try:
        return Path(file_path).read_bytes()
    except OSError as error:
        raise LinediffInputError(
            "Cannot read Git operand '{}': {}".format(file_path, error.strerror or error)
        ) from error


def read_stdin_content() -> str:
    try:
        content = sys.stdin.buffer.read().decode('utf-8')
    except UnicodeDecodeError as error:
        raise LinediffInputError("Cannot decode stdin as UTF-8") from error
    except OSError as error:
        raise LinediffInputError("Cannot read stdin: {}".format(error)) from error
    if '\x00' in content:
        raise LinediffInputError("Binary stdin contains NUL bytes")
    return content


def parse_pair_stdin(content: str) -> Tuple[str, str, str, str]:
    """Split the legacy pair format without changing either text's line endings."""
    separator = re.search(r'(?m)^---(?:\r?\n|$)', content)
    if separator is None:
        raise LinediffInputError("Stdin must contain a line with only '---' between the two texts")
    return content[:separator.start()], content[separator.end():], 'old', 'new'
