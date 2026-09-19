from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional, Union
import heapq
from collections import defaultdict
import difflib

from .model import Atom, ListNode

# Graph-based Structural Diffing
@dataclass
class Vertex:
    """Represents a vertex in the diff graph."""
    node: Optional[Union[ListNode, Atom]]
    side: str  # 'left' or 'right'
    index: int

    def __hash__(self):
        return hash((self.side, self.index))

    def __eq__(self, other):
        return isinstance(other, Vertex) and self.side == other.side and self.index == other.index

@dataclass
class Edge:
    """Represents an edge in the diff graph with cost."""
    from_vertex: Vertex
    to_vertex: Vertex
    cost: int
    operation: str  # 'match', 'insert', 'delete', 'change'

class DiffEngine:
    """Core diff engine implementing structural and linear diffing."""

    def __init__(self):
        self.graph: Dict[Vertex, List[Edge]] = defaultdict(list)

    def build_graph(self, left_tree: ListNode, right_tree: ListNode) -> None:
        """Build the diff graph from two syntax trees."""
        self.graph.clear()
        left_vertices = self._create_vertices(left_tree, 'left')
        right_vertices = self._create_vertices(right_tree, 'right')

        # Create edges for matches, inserts, deletes
        for lv in left_vertices:
            for rv in right_vertices:
                if self._nodes_similar(lv.node, rv.node):
                    self.graph[lv].append(Edge(lv, rv, 0, 'match'))  # No cost for match
                else:
                    self.graph[lv].append(Edge(lv, rv, 1, 'change'))  # Cost for change

        # Add delete edges (from left to dummy end)
        end_vertex = Vertex(None, 'end', -1)  # Dummy end vertex
        for lv in left_vertices:
            self.graph[lv].append(Edge(lv, end_vertex, 1, 'delete'))

        # Add insert edges (from dummy start to right)
        start_vertex = Vertex(None, 'start', -1)  # Dummy start vertex
        for rv in right_vertices:
            self.graph[start_vertex].append(Edge(start_vertex, rv, 1, 'insert'))

        self.start_vertex = start_vertex
        self.end_vertex = end_vertex

    def _create_vertices(self, tree: ListNode, side: str) -> List[Vertex]:
        """Recursively create vertices for leaf (Atom) nodes in the tree."""
        vertices = []
        index = 0
        def traverse(node: Union[ListNode, Atom], pos: int):
            nonlocal index
            if isinstance(node, Atom):
                vertex = Vertex(node, side, index)
                vertices.append(vertex)
                index += 1
            elif isinstance(node, ListNode):
                for child in node.children:
                    traverse(child, pos)
        traverse(tree, 0)
        return vertices

    def _nodes_similar(self, node1: Union[ListNode, Atom], node2: Union[ListNode, Atom]) -> bool:
        """Check if two nodes are similar for matching.

        For Atoms, compares their values.
        For ListNodes, compares the number of children (basic structural similarity).
        """
        if type(node1) != type(node2):
            return False
        if isinstance(node1, Atom):
            return node1.value == node2.value  # type: ignore
        # For ListNode, could check structure, but for now simple equality
        return len(node1.children) == len(node2.children)  # type: ignore

    def dijkstra_shortest_path(self, start: Vertex, end: Vertex) -> List[Edge]:
        """Find optimal path using Dijkstra's algorithm."""
        distances: Dict[Vertex, int] = {vertex: float('inf') for vertex in self.graph}
        distances[start] = 0
        previous: Dict[Vertex, Optional[Edge]] = {vertex: None for vertex in self.graph}
        pq = [(0, id(start), start)]  # (distance, id, vertex) to make comparable
        visited: Set[Vertex] = set()
        counter = 0

        while pq:
            current_distance, _, current_vertex = heapq.heappop(pq)

            if current_vertex in visited:
                continue
            visited.add(current_vertex)

            if current_vertex == end:
                break

            for edge in self.graph.get(current_vertex, []):
                neighbor = edge.to_vertex
                if neighbor in visited:
                    continue
                new_distance = current_distance + edge.cost
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    previous[neighbor] = edge
                    counter += 1
                    heapq.heappush(pq, (new_distance, counter, neighbor))

        # Reconstruct path
        path = []
        current = end
        while current != start and previous.get(current):
            edge = previous[current]
            path.append(edge)
            current = edge.from_vertex
        path.reverse()
        return path

    def lcs_linear(self, left: List[str], right: List[str]) -> List[Tuple[int, int]]:
        """Longest Common Subsequence for linear diffs."""
        m, n = len(left), len(right)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Fill dp table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if left[i - 1] == right[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # Backtrack to find LCS
        lcs = []
        i, j = m, n
        while i > 0 and j > 0:
            if left[i - 1] == right[j - 1]:
                lcs.append((i - 1, j - 1))
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        lcs.reverse()
        return lcs

    def align_sequences(self, left: List[str], right: List[str]) -> List[Tuple[str, str]]:
        """Basic alignment/slider correction logic."""
        lcs = self.lcs_linear(left, right)
        aligned = []
        i = j = 0
        for li, rj in lcs:
            # Add non-matching parts
            while i < li:
                aligned.append((left[i], ''))
                i += 1
            while j < rj:
                aligned.append(('', right[j]))
                j += 1
            # Add matching part
            aligned.append((left[i], right[j]))
            i += 1
            j += 1
        # Add remaining
        while i < len(left):
            aligned.append((left[i], ''))
            i += 1
        while j < len(right):
            aligned.append(('', right[j]))
            j += 1
        return aligned

    def fallback_diff(self, left_lines: List[str], right_lines: List[str]) -> List[str]:
        """Return unified records, preserving CRLF and missing-final-LF markers.

        Inputs must retain their original line endings (``splitlines(True)``).
        The renderer owns the final newline between output records.
        """
        records = []
        for index, record in enumerate(
            difflib.unified_diff(left_lines, right_lines, lineterm='\n')
        ):
            if record.endswith('\n'):
                records.append(record[:-1])
            else:
                records.append(record)
                if index >= 2 and record[:1] in (' ', '+', '-'):
                    records.append('\\ No newline at end of file')
        return records

from .parser import TREE_SITTER_AVAILABLE, parse_to_tree as ts_parse_to_tree

TREE_SITTER_PARSER_AVAILABLE = TREE_SITTER_AVAILABLE

# Utility functions
def count_nodes(node: Union[ListNode, Atom]) -> int:
    """Count the total number of nodes in the tree."""
    if isinstance(node, Atom):
        return 1
    return 1 + sum(count_nodes(child) for child in node.children)

def parse_to_tree(content: str, file_path: Optional[str] = None) -> ListNode:
    """Parse content into syntax tree using tree-sitter if available, fallback to basic parsing."""
    return ts_parse_to_tree(content, file_path)

def compute_diff(left_content: str, right_content: str, left_file_path: Optional[str] = None, right_file_path: Optional[str] = None) -> List[str]:
    """Compute an exact text diff; structural rendering is added separately."""
    if left_content == right_content:
        return []
    return DiffEngine().fallback_diff(
        left_content.splitlines(keepends=True),
        right_content.splitlines(keepends=True),
    )
