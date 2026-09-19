from linediff.diff import compute_diff, parse_to_tree, DiffEngine, Atom, ListNode
from linediff.parser import parse_to_tree as parser_parse_to_tree


def test_parse_to_tree_basic():
    """Test basic parsing to tree."""
    content = "line1\nline2\n"
    tree = parse_to_tree(content)
    assert isinstance(tree, ListNode)
    assert len(tree.children) == 2
    assert all(isinstance(child, Atom) for child in tree.children)


def test_compute_diff_identical():
    """Test diff of identical content."""
    content = "hello\nworld\n"
    diff = compute_diff(content, content)
    assert diff == []  # No differences


def test_compute_diff_simple():
    """Test simple diff."""
    left = "line1\nline2\n"
    right = "line1\nmodified\n"
    diff = compute_diff(left, right)
    assert diff[2] == "@@ -1,2 +1,2 @@"
    assert "-line2" in diff
    assert "+modified" in diff


def test_diff_engine_lcs():
    """Test LCS algorithm."""
    engine = DiffEngine()
    left = ["a", "b", "c"]
    right = ["a", "x", "b", "c"]
    lcs = engine.lcs_linear(left, right)
    assert lcs == [(0, 0), (1, 2), (2, 3)]


def test_atom_dataclass():
    """Test Atom dataclass."""
    atom = Atom("test", 0)
    assert atom.value == "test"
    assert atom.position == 0


def test_listnode_dataclass():
    """Test ListNode dataclass."""
    atom1 = Atom("child1", 0)
    atom2 = Atom("child2", 1)
    listnode = ListNode([atom1, atom2], 0)
    assert len(listnode.children) == 2
    assert listnode.position == 0


def test_count_nodes():
    """Test count_nodes utility."""
    from linediff.diff import count_nodes

    atom = Atom("test", 0)
    assert count_nodes(atom) == 1
    listnode = ListNode([atom], 0)
    assert count_nodes(listnode) == 2


def test_fallback_diff():
    """Test fallback diff."""
    engine = DiffEngine()
    left = ["line1\n", "line2\n"]
    right = ["line1\n", "modified\n"]
    diff = engine.fallback_diff(left, right)
    assert diff[2] == "@@ -1,2 +1,2 @@"
    assert "-line2" in diff
    assert "+modified" in diff


def test_parser_fallback():
    """Test parser fallback."""
    tree = parser_parse_to_tree("content\n")
    assert isinstance(tree, ListNode)
