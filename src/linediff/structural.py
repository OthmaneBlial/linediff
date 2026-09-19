"""Python definition changes for the human-readable structural view.

The module uses Python's standard AST. It never replaces the exact text diff.
When parsing fails or matching is ambiguous, callers must show the text diff
and the fallback reason instead of claiming a structural result.
"""

import ast
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Set, Tuple

from .diff import DiffEngine
from .limits import MAX_STRUCTURAL_BYTES, MAX_DEFINITIONS


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
    parser_backend: str = 'python-ast'


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
    return {before[old_index] for old_index, _ in DiffEngine().lcs_linear(before, after)}


def _tree_sitter_ranges(tree: object, source: str) -> Dict[str, Tuple[int, int]]:
    """Locate indexed Python definitions using Tree-sitter byte-based nodes."""
    source_bytes = source.encode('utf-8')
    ranges: Dict[str, Tuple[int, int]] = {}

    def unwrap(node: object) -> object:
        if node.type == 'decorated_definition':
            for child in node.named_children:
                if child.type in ('function_definition', 'class_definition'):
                    return child
        return node

    def register(node: object, prefix: str = '') -> None:
        actual = unwrap(node)
        if actual.type not in ('function_definition', 'class_definition'):
            return
        name_node = actual.child_by_field_name('name')
        if name_node is None:
            return
        name = source_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8')
        qualified = prefix + name
        last_line = node.end_point.row + (1 if node.end_point.column else 0)
        ranges[qualified] = (node.start_point.row + 1, max(node.start_point.row + 1, last_line))
        if actual.type == 'class_definition':
            body = actual.child_by_field_name('body')
            if body is not None:
                for child in body.named_children:
                    if unwrap(child).type == 'function_definition':
                        register(child, qualified + '.')

    for child in tree.root_node.named_children:
        register(child)
    return ranges


def _tree_sitter_positions(before: str, after: str, old_units: Dict[str, Definition],
                           new_units: Dict[str, Definition]) -> Optional[Tuple[Dict[str, Definition], Dict[str, Definition]]]:
    from .parser import get_parser

    parser = get_parser()
    old_tree = parser.parse_raw(before, language='python')
    new_tree = parser.parse_raw(after, language='python')
    if old_tree is None or new_tree is None:
        return None
    if old_tree.root_node.has_error or new_tree.root_node.has_error:
        return None
    old_ranges = _tree_sitter_ranges(old_tree, before)
    new_ranges = _tree_sitter_ranges(new_tree, after)
    if not set(old_units).issubset(old_ranges) or not set(new_units).issubset(new_ranges):
        return None
    positioned_old = {
        name: replace(unit, start_line=old_ranges[name][0], end_line=old_ranges[name][1])
        for name, unit in old_units.items()
    }
    positioned_new = {
        name: replace(unit, start_line=new_ranges[name][0], end_line=new_ranges[name][1])
        for name, unit in new_units.items()
    }
    return positioned_old, positioned_new


def analyze_python_changes(before: str, after: str) -> StructuralResult:
    """Describe changed Python definitions without suppressing text changes."""
    if max(len(before.encode('utf-8')), len(after.encode('utf-8'))) > MAX_STRUCTURAL_BYTES:
        return StructuralResult(False, (), 'Python structural view exceeds the 1 MiB input limit')
    try:
        old_tree = ast.parse(before)
        new_tree = ast.parse(after)
    except (SyntaxError, ValueError, RecursionError) as error:
        return StructuralResult(False, (), 'Python parsing failed: {}'.format(error))

    old_units, old_order, old_duplicate = _collect(old_tree)
    new_units, new_order, new_duplicate = _collect(new_tree)
    if max(len(old_order), len(new_order)) > MAX_DEFINITIONS:
        return StructuralResult(False, (), 'Python structural view exceeds 500 top-level definitions')
    if old_duplicate or new_duplicate:
        return StructuralResult(False, (), 'Repeated definition names make matching ambiguous')

    backend = 'python-ast'
    positioned = _tree_sitter_positions(before, after, old_units, new_units)
    if positioned is not None:
        old_units, new_units = positioned
        backend = 'tree-sitter + python-ast'

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
    return StructuralResult(True, tuple(changes), parser_backend=backend)
