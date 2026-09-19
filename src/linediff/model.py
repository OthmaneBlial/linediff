"""Small syntax-tree value types shared by parsing and diff modules."""

from dataclasses import dataclass
from typing import List, Union


@dataclass
class Atom:
    """Atomic source element and its position within the parsed input."""

    value: str
    position: int


@dataclass
class ListNode:
    """Container of syntax elements and its position within the parsed input."""

    children: List[Union['ListNode', Atom]]
    position: int
