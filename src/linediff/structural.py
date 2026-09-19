"""Python definition changes for the human-readable structural view.

The module uses Python's standard AST. It never replaces the exact text diff.
When parsing fails or matching is ambiguous, callers must show the text diff
and the fallback reason instead of claiming a structural result.
"""

import ast
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


@dataclass(frozen=True)
class Definition:
    name: str
    kind: str
    start_line: int
    end_line: int
    fingerprint: str
    signature: str
    body: str
    order: int
    top_level: bool


@dataclass(frozen=True)
class StructuralChange:
    kind: str  # added, removed, changed, moved
    definition: str
    old_lines: Optional[Tuple[int, int]]
    new_lines: Optional[Tuple[int, int]]
    details: Tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuralResult:
    supported: bool
    changes: Tuple[StructuralChange, ...]
    reason: Optional[str] = None


def _dump(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def _function_signature(node: ast.AST) -> str:
    return repr(
        (
            isinstance(node, ast.AsyncFunctionDef),
            _dump(node.args),
            _dump(node.returns) if node.returns is not None else None,
            tuple(_dump(item) for item in node.decorator_list),
        )
    )


def _definition(name: str, kind: str, node: ast.AST, order: int, top_level: bool) -> Definition:
    if isinstance(node, FUNCTION_NODES):
        signature = _function_signature(node)
        body = repr(tuple(_dump(item) for item in node.body))
    else:
        signature = repr(
            (
                tuple(_dump(item) for item in node.bases),
                tuple(_dump(item) for item in node.keywords),
                tuple(_dump(item) for item in node.decorator_list),
            )
        )
        body = repr(tuple(_dump(item) for item in node.body if not isinstance(item, FUNCTION_NODES)))
    fingerprint = repr((signature, body))
    return Definition(
        name=name,
        kind=kind,
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        fingerprint=fingerprint,
        signature=signature,
        body=body,
        order=order,
        top_level=top_level,
    )


def _collect(tree: ast.Module) -> Tuple[Dict[str, Definition], List[str], bool]:
    definitions: Dict[str, Definition] = {}
    top_level_names = []
    duplicate = False
    for order, node in enumerate(tree.body):
        if isinstance(node, FUNCTION_NODES):
            name = node.name
            unit = _definition(name, 'function', node, order, True)
        elif isinstance(node, ast.ClassDef):
            name = node.name
            unit = _definition(name, 'class', node, order, True)
        else:
            continue
        if name in definitions:
            duplicate = True
        definitions[name] = unit
        top_level_names.append(name)
        if isinstance(node, ast.ClassDef):
            for method_order, child in enumerate(node.body):
                if isinstance(child, FUNCTION_NODES):
                    qualified = name + '.' + child.name
                    if qualified in definitions:
                        duplicate = True
                    definitions[qualified] = _definition(qualified, 'method', child, method_order, False)
    return definitions, top_level_names, duplicate


def _ordered_anchors(before: List[str], after: List[str]) -> Set[str]:
    """Find definitions that retain relative order; non-anchors may be moves."""
    rows = len(before) + 1
    columns = len(after) + 1
    scores = [[0] * columns for _ in range(rows)]
    for old_index in range(len(before) - 1, -1, -1):
        for new_index in range(len(after) - 1, -1, -1):
            if before[old_index] == after[new_index]:
                scores[old_index][new_index] = 1 + scores[old_index + 1][new_index + 1]
            else:
                scores[old_index][new_index] = max(
                    scores[old_index + 1][new_index], scores[old_index][new_index + 1]
                )
    anchors: Set[str] = set()
    old_index = new_index = 0
    while old_index < len(before) and new_index < len(after):
        if before[old_index] == after[new_index]:
            anchors.add(before[old_index])
            old_index += 1
            new_index += 1
        elif scores[old_index + 1][new_index] >= scores[old_index][new_index + 1]:
            old_index += 1
        else:
            new_index += 1
    return anchors


def analyze_python_changes(before: str, after: str) -> StructuralResult:
    """Describe changed Python definitions without suppressing text changes."""
    try:
        old_tree = ast.parse(before)
        new_tree = ast.parse(after)
    except (SyntaxError, ValueError, RecursionError) as error:
        return StructuralResult(False, (), 'Python parsing failed: {}'.format(error))

    old_units, old_order, old_duplicate = _collect(old_tree)
    new_units, new_order, new_duplicate = _collect(new_tree)
    if old_duplicate or new_duplicate:
        return StructuralResult(False, (), 'Repeated definition names make matching ambiguous')

    anchors = _ordered_anchors(old_order, new_order)
    changes = []
    for name, old in old_units.items():
        if name not in new_units:
            changes.append(StructuralChange('removed', name, (old.start_line, old.end_line), None))
    for name, new in new_units.items():
        old = old_units.get(name)
        if old is None:
            changes.append(StructuralChange('added', name, None, (new.start_line, new.end_line)))
            continue
        if old.kind != new.kind:
            changes.append(StructuralChange('removed', name, (old.start_line, old.end_line), None))
            changes.append(StructuralChange('added', name, None, (new.start_line, new.end_line)))
            continue
        details = []
        if old.signature != new.signature:
            details.append('signature')
        if old.body != new.body:
            details.append('body')
        if old.fingerprint != new.fingerprint:
            changes.append(
                StructuralChange(
                    'changed', name, (old.start_line, old.end_line),
                    (new.start_line, new.end_line), tuple(details),
                )
            )
        if old.top_level and new.top_level and name not in anchors:
            changes.append(
                StructuralChange('moved', name, (old.start_line, old.end_line), (new.start_line, new.end_line))
            )

    changes.sort(key=lambda item: (
        item.new_lines[0] if item.new_lines else item.old_lines[0],
        item.definition,
        item.kind,
    ))
    return StructuralResult(True, tuple(changes))
