"""Read user-supplied file and stdin operands without changing their bytes."""

import os
import re
import stat
import sys
import unicodedata
from pathlib import Path
from typing import Tuple
from .limits import MAX_INPUT_BYTES, DiffLimitError


class LinediffInputError(Exception):
    """An input cannot be compared as UTF-8 text."""


BIDI_CONTROLS = {
    "\u061c",
    "\u200e",
    "\u200f",
    *map(chr, range(0x202A, 0x202F)),
    *map(chr, range(0x2066, 0x206A)),
}


def unsafe_character(content: str, path: bool = False):
    """Return the first control that could spoof terminal output."""
    for index, char in enumerate(content):
        if char in BIDI_CONTROLS:
            return "U+{:04X}".format(ord(char))
        if unicodedata.category(char) == "Cc":
            if not path and (
                char in "\n\t"
                or char == "\r"
                and index + 1 < len(content)
                and content[index + 1] == "\n"
            ):
                continue
            return "U+{:04X}".format(ord(char))
    return None


def validate_label(label: str) -> None:
    unsafe = unsafe_character(label, path=True)
    if unsafe:
        raise LinediffInputError(
            "File path contains terminal control {}".format(unsafe)
        )


def _read_regular_bytes(file_path: str, label: str) -> bytes:
    validate_label(file_path)
    try:
        metadata = Path(file_path).stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise LinediffInputError(
                "Cannot read {} '{}': not a regular file".format(label, file_path)
            )
        if metadata.st_size > MAX_INPUT_BYTES:
            raise DiffLimitError(
                "{} '{}' exceeds the 4 MiB input limit".format(label, file_path)
            )
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(file_path, flags), "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise LinediffInputError(
                    "Cannot read {} '{}': not a regular file".format(label, file_path)
                )
            data = stream.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise DiffLimitError(
                "{} '{}' exceeds the 4 MiB input limit".format(label, file_path)
            )
        return data
    except OSError as error:
        raise LinediffInputError(
            "Cannot read '{}': {}".format(file_path, error.strerror or error)
        ) from error


def read_file_content(file_path: str) -> str:
    data = _read_regular_bytes(file_path, "Text file")
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LinediffInputError(
            "Cannot decode '{}' as UTF-8".format(file_path)
        ) from error
    if "\x00" in content:
        raise LinediffInputError(
            "Binary file '{}' contains NUL bytes".format(file_path)
        )
    unsafe = unsafe_character(content)
    if unsafe:
        raise LinediffInputError(
            "Text file contains terminal control {}".format(unsafe)
        )
    return content


def read_git_bytes(file_path: str) -> bytes:
    """Read a Git external-diff operand, including its null-file sentinel."""
    if file_path == "/dev/null":
        return b""
    return _read_regular_bytes(file_path, "Git operand")


def read_stdin_content() -> str:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES * 2 + 1)
        if len(raw) > MAX_INPUT_BYTES * 2:
            raise DiffLimitError("Stdin exceeds the 8 MiB pair input limit")
        content = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LinediffInputError("Cannot decode stdin as UTF-8") from error
    except OSError as error:
        raise LinediffInputError("Cannot read stdin: {}".format(error)) from error
    if "\x00" in content:
        raise LinediffInputError("Binary stdin contains NUL bytes")
    unsafe = unsafe_character(content)
    if unsafe:
        raise LinediffInputError("Stdin contains terminal control {}".format(unsafe))
    return content


def parse_pair_stdin(content: str) -> Tuple[str, str, str, str]:
    """Split the legacy pair format without changing either text's line endings."""
    separator = re.search(r"(?m)^---(?:\r?\n|$)", content)
    if separator is None:
        raise LinediffInputError(
            "Stdin must contain a line with only '---' between the two texts"
        )
    return content[: separator.start()], content[separator.end() :], "old", "new"
