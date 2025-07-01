from functools import lru_cache
import fibheap as fh
import sys

from typing import Optional

from fandango.language.symbol import NonTerminal
from fandango.language.grammar import Grammar

from fdlearn.data import FandangoInput
from fdlearn.reduction.transformer import NonTerminalVisitor


def _is_string_numeric(value: str) -> tuple[bool, float | None]:
    """
    Safely checks if a string can be converted to a float.

    Returns a tuple of (bool, float or None). This avoids converting twice.
    """
    try:
        return True, float(value)
    except (ValueError, TypeError):
        return False, None


def _find_longest_common_substring(strings: list[str]) -> str:
    """
    Finds the longest common substring among a list of strings.
    """
    if not strings:
        return ""

    shortest_str = min(strings, key=len)
    n = len(shortest_str)

    for length in range(n, 0, -1):
        for start in range(n - length + 1):
            substring = shortest_str[start : start + length]
            if all(substring in s for s in strings):
                return substring
    return ""


class ValueMap:
    """
    Extracts and stores string and numeric values associated with specific
    non-terminals from a set of input data.
    """

    def __init__(self, relevant_non_terminals: set[NonTerminal]):
        """Initializes the storage for non-terminal values."""
        self.relevant_non_terminals = relevant_non_terminals
        self._string_values: dict[NonTerminal, set[str]] = {
            nt: set() for nt in relevant_non_terminals
        }
        self._numeric_values: dict[NonTerminal, set[float]] = {
            nt: set() for nt in relevant_non_terminals
        }

    @classmethod
    def from_inputs(
        cls, relevant_non_terminals: set[NonTerminal], inputs: set[FandangoInput]
    ) -> "ValueMap":
        """
        A factory method to create an instance and populate it from inputs.
        """
        instance = cls(relevant_non_terminals)
        instance._populate_values(inputs)
        return instance

    def _populate_values(self, inputs: set[FandangoInput]) -> None:
        """
        Extracts and categorizes values from inputs for relevant non-terminals.
        This method modifies the instance's state.
        """
        for non_terminal in self.relevant_non_terminals:
            all_values_as_strings = []
            for input_obj in inputs:
                found_trees = input_obj.tree.find_all_trees(non_terminal)
                for tree in found_trees:
                    value_str = str(tree)
                    all_values_as_strings.append(value_str)

                    is_numeric, numeric_val = _is_string_numeric(value_str)
                    if is_numeric:
                        self._numeric_values[non_terminal].add(numeric_val)
                    else:
                        self._string_values[non_terminal].add(value_str)

            if len(all_values_as_strings) > 1:
                lcs = _find_longest_common_substring(all_values_as_strings)
                if len(lcs) >= 2:
                    self._string_values[non_terminal].add(lcs)

    @property
    def string_values(self) -> dict[NonTerminal, set[str]]:
        """Returns all collected string values."""
        return self._string_values

    @property
    def numeric_values(self) -> dict[NonTerminal, set[float]]:
        """Returns all collected numeric values."""
        return self._numeric_values

    @property
    def filtered_numeric_values(self) -> dict[NonTerminal, set[float]]:
        """
        Returns a map containing only the min and max numeric values
        for each non-terminal.
        """
        reduced_values = {}
        for non_terminal, values in self._numeric_values.items():
            if values:
                reduced_values[non_terminal] = {min(values), max(values)}
        return reduced_values


def get_reachability_map_level(
    grammar: Grammar,
) -> dict[NonTerminal, dict[int, set[NonTerminal]]]:
    """
    Get the reachability map for a given grammar.

    :param grammar: The grammar to get the reachability map for.
    :return: The reachability map.s
    """
    reachability_map = dict()
    for non_terminal in grammar.rules:
        reachability_map[non_terminal] = get_reachable_non_terminals_level(
            grammar, non_terminal
        )

    return reachability_map


def get_reachable_non_terminals_level(
    grammar: Grammar, non_terminal: NonTerminal
) -> dict[int, set[NonTerminal]]:
    """
    Get all reachable non-terminals for a given non-terminal in a grammar.

    :param grammar: The grammar to search in.
    :param non_terminal: The non-terminal to search for.
    :return: A set of reachable non-terminals.
    """
    reachable: dict[int, set[NonTerminal]] = dict()
    already_reached: set[NonTerminal] = set()
    non_terminal_visitor = NonTerminalVisitor()

    def _find_reachable_nonterminals(
        grammar_: Grammar, symbol: NonTerminal, level_: int
    ):
        nonlocal reachable
        if level_ not in reachable:
            reachable[level_] = set()

        reachable[level_].add(symbol)
        already_reached.add(symbol)

        if symbol == non_terminal:
            return
        expansion_node = grammar_.rules.get(symbol, [])
        for exp in non_terminal_visitor.visit(expansion_node):
            if exp not in reachable and exp != symbol and not exp in already_reached:
                _find_reachable_nonterminals(grammar_, exp, level_=level_ + 1)

    level = 0
    expansion = grammar.rules.get(non_terminal, [])
    for exp in non_terminal_visitor.visit(expansion):
        _find_reachable_nonterminals(grammar, exp, level_=level)
    return reachable


from collections import defaultdict, deque


def get_reachable_non_terminals_level_new(
    grammar: Grammar, non_terminal: str
) -> dict[int, set[str]]:
    """
    Correctly gets all reachable non-terminals grouped by their minimum
    derivation level using a Breadth-First Search (BFS).
    """
    non_terminal_visitor = NonTerminalVisitor()
    # Queue stores (non_terminal, level)
    queue = deque([(non_terminal, 0)])

    # visited tracks nodes for which we've found the shortest path
    visited = {non_terminal}

    level_map = defaultdict(set)
    level_map[0].add(non_terminal)

    while queue:
        current_nt, current_level = queue.popleft()

        expansion_node = grammar.rules.get(current_nt, [])
        for exp in non_terminal_visitor.visit(expansion_node):
            if exp not in visited:
                visited.add(exp)
                new_level = current_level + 1
                level_map[new_level].add(exp)
                queue.append((exp, new_level))

    return dict(level_map)


class ReachabilityMap:
    """
    A class to represent a reachability map for non-terminals in a grammar.
    It provides methods to compute the shortest path between two non-terminals.
    """

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.map = get_reachability_map_level(grammar)

    def get_reachable_non_terminals(
        self, non_terminal: NonTerminal
    ) -> dict[int, set[NonTerminal]] | dict:
        return self.map.get(non_terminal, {})

    @lru_cache(maxsize=None)
    def _shortest_path(
        self, source: NonTerminal, target: NonTerminal
    ) -> list[NonTerminal]:

        dist, prev = self.dijkstra(source, target)
        s = []
        u = target
        if u == source or prev[u] is not None:
            while u is not None:
                s = [u] + s
                u = None if u == source else prev[u]

        return s

    def shortest_path(
        self,
        source: NonTerminal,
        target: NonTerminal,
    ) -> list[NonTerminal]:
        result = self._shortest_path(source, target)
        return result

    def dijkstra(
        self, source: NonTerminal, target: Optional[NonTerminal] = None
    ) -> tuple[dict[NonTerminal, int], dict[NonTerminal, Optional[NonTerminal]]]:
        """Implementation of Dijkstra's algorithm with Fibonacci heap"""
        fh_node_map: dict[NonTerminal, fh.Node] = {}
        fh_rev_node_map: dict[fh.Node, NonTerminal] = {}

        dist: dict[NonTerminal, int] = {source: 0}
        prev: dict[NonTerminal, Optional[NonTerminal]] = {}

        q: fh.Fheap = fh.makefheap()

        for v in self.map.keys():
            if v != source:
                dist[v] = sys.maxsize
                prev[v] = None

            fh_node = fh.Node(dist[v])
            fh_node_map[v] = fh_node
            fh_rev_node_map[fh_node] = v
            q.insert(fh_node)

        while q.num_nodes:
            u: NonTerminal = fh_rev_node_map[q.extract_min()]

            if u == target:
                break

            if issubclass(type(u), NonTerminal):
                u: NonTerminal
                for v in self.map[u].get(0, set()):
                    alt = dist[u] + 1
                    if alt < dist[v]:
                        dist[v] = alt
                        prev[v] = u
                        q.decrease_key(fh_node_map[v], alt)

        return dist, prev

    def _bfs_for_shortest_paths(self, source: NonTerminal) -> (
            (dict[NonTerminal, int], dict[NonTerminal, list[NonTerminal]])
    ):
        """
        Performs a BFS to find shortest path lengths and all predecessors.

        Returns:
            dist (dict): Shortest distance from source to each node.
            predecessors (dict): Maps each node to a list of its predecessors
                                 on a shortest path.
        """
        dist = {node: float('inf') for node in self.grammar.rules.keys()}
        predecessors = {node: [] for node in self.grammar.rules.keys()}

        dist[source] = 0
        queue = deque([source])

        while queue:
            u = queue.popleft()

            for v in self.map[u].get(0, set()):
                # A shorter path is found. This is the first time we reach v
                # via a shortest path.
                if dist[v] > dist[u] + 1:
                    dist[v] = dist[u] + 1
                    predecessors[v].append(u)
                    queue.append(v)
                # Another path of the same shortest length is found.
                elif dist[v] == dist[u] + 1:
                    predecessors[v].append(u)

        return dist, predecessors

    def _reconstruct_paths(
            self, source: NonTerminal, target: NonTerminal, predecessors: dict[NonTerminal, list[NonTerminal]]
    ) -> list[list[NonTerminal]]:
        """Recursively reconstructs all paths from source to target."""
        all_paths = []

        def find_paths_recursive(current_path):
            last_node = current_path[0]
            if last_node == source:
                all_paths.append(current_path)
                return

            for pred in predecessors[last_node]:
                find_paths_recursive([pred] + current_path)

        find_paths_recursive([target])
        return all_paths

    def get_all_shortest_paths(
            self, source: NonTerminal, target: NonTerminal
    ) -> list[list[NonTerminal]]:
        """
        Returns a list of all shortest paths from source to target.
        Each path is a list of NonTerminals.
        """

        dist, predecessors = self._bfs_for_shortest_paths(source)

        # If target is unreachable, its distance will be infinity
        if dist[target] == float('inf'):
            return []

        return self._reconstruct_paths(source, target, predecessors)