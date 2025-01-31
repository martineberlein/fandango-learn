import logging
from abc import ABC, abstractmethod
from typing import Generator, Collection, Optional
import random
from copy import deepcopy

from debugging_framework.input.oracle import OracleResult
from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal
from fandango.language.tree import DerivationTree

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.types import OracleType


LOGGER = logging.getLogger("fandango-mutation-fuzzer")
Path = tuple[int, ...]


class Operator(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def replace(
        self, inp: DerivationTree, path: Path, **kwargs
    ) -> DerivationTree | None:
        raise NotImplementedError()


class ReplaceFragmentOperator(Operator):

    def __init__(self, fragments: dict[NonTerminal, set[DerivationTree]]):
        super().__init__()

    def replace(
        self,
        inp: DerivationTree,
        path: Path,
        fragments: dict[NonTerminal, set[DerivationTree]] = dict,
        **kwargs,
    ) -> DerivationTree | None:
        subtree = get_subtree(inp, path)
        if not isinstance(subtree.symbol, NonTerminal):
            return None

        different_fragments = [
            fragment
            for fragment in fragments.get(subtree.symbol, [])
            if fragment and not str(fragment) == str(subtree)
        ]

        if not different_fragments:
            return None

        fragment = random.choice(different_fragments)
        result = replace_subtree(inp, path, fragment)
        return result


class ReplaceRandomSubtreeOperator(Operator):

    def __init__(self, grammar: Grammar):
        super().__init__()
        self.grammar = grammar

    def replace(
        self, inp: DerivationTree, path: Path, **kwargs
    ) -> DerivationTree | None:
        subtree = get_subtree(inp, path)
        if not isinstance(subtree.symbol, NonTerminal):
            return None

        new_subtree = self.grammar.fuzz(subtree.symbol)

        if subtree == new_subtree:
            return None

        return replace_subtree(inp, path, new_subtree)


class SwapSubtreeOperator(Operator):

    def __init__(self):
        super().__init__()

    def replace(
        self, inp: DerivationTree, path: Path, **kwargs
    ) -> DerivationTree | None:
        subtree = get_subtree(inp, path)
        if not isinstance(subtree.symbol, NonTerminal):
            return None

        matches = [
            tree for tree in inp.find_all_trees(subtree.symbol) if tree != subtree
        ]

        if not matches:
            return None

        result = replace_subtree(inp, path, random.choice(matches))
        return result


def traverse(tree: DerivationTree, action, path: Path = ()):
    action(path, tree)
    for i, child in enumerate(tree.children):
        traverse(child, action, path + (i,))


def get_paths(tree: DerivationTree) -> list[tuple[Path, DerivationTree]]:
    result: list[tuple[Path, DerivationTree]] = []

    def action(path, node):
        result.append((path, node))

    traverse(tree, action)
    return result


def get_subtree(tree: DerivationTree, path: tuple[int, ...]):
    curr_node = tree
    while path:
        if not curr_node.children:
            return None

        curr_node = curr_node.children[path[0]]
        path = path[1:]

    return curr_node


def replace_subtree(
    tree: DerivationTree, path: tuple[int, ...], subtree: DerivationTree
) -> DerivationTree:
    if not path:
        return deepcopy(subtree)  # If path is empty, replace the entire tree

    def helper(node: DerivationTree, current_path: tuple[int, ...]) -> DerivationTree:
        if not current_path:  # If we reached the target node, return the new subtree
            return deepcopy(subtree)

        if not node.children or current_path[0] >= len(node.children):
            return deepcopy(node)  # If invalid path, return a copy of the node

        new_children = list(node.children)
        new_children[current_path[0]] = helper(
            node.children[current_path[0]], current_path[1:]
        )

        return DerivationTree(node.symbol, new_children)

    return helper(tree, path)


class MutationFuzzer:

    def __init__(
        self,
        grammar: Grammar,
        seed_inputs: Collection[FandangoInput],
        oracle: Optional[OracleType] = None,
        min_mutation: int = 2,
        max_mutations: int = 10,
    ):
        self.grammar = grammar
        self.seed_inputs = seed_inputs
        self.oracle = oracle
        self.min_mutations = min_mutation
        self.max_mutations = max_mutations

        self.population: set[FandangoInput] = set()
        self.fragments: dict[NonTerminal, set[DerivationTree]] = {}

        self.reset()

        self.mutation_operators = [
            ReplaceFragmentOperator(self.fragments),
            ReplaceRandomSubtreeOperator(self.grammar),
            SwapSubtreeOperator(),
        ]

    def reset(self):
        self.population: set[FandangoInput] = set(self.seed_inputs)
        self.fragments = {}

        for seed in self.population:
            self.update_fragments(seed)

    def update_fragments(self, inp: FandangoInput):
        for _, subtree in get_paths(inp.tree):
            if isinstance(subtree.symbol, NonTerminal):
                self.fragments.setdefault(subtree.symbol, set()).add(subtree)

    def fuzz(self) -> FandangoInput:
        num_mutations = random.randint(self.min_mutations, self.max_mutations)
        curr_inp = random.choice(list(self.population))
        mutations = 0
        while mutations < num_mutations:
            maybe_result = self.mutate(curr_inp)
            if maybe_result is not None:
                curr_inp = maybe_result
                mutations += 1
        return curr_inp

    def mutate(self, inp: FandangoInput) -> FandangoInput | None:
        tree = inp.tree
        paths = [
            path
            for path, subtree in get_paths(inp.tree)
            if isinstance(subtree.symbol, NonTerminal)
        ]

        random.shuffle(paths)  # Randomize order to avoid bias

        for path in paths:
            operator: Operator = random.choice(self.mutation_operators)
            new_tree = operator.replace(tree, path, fragments=self.fragments)
            if new_tree is not None:
                return FandangoInput(tree=new_tree)

        return None

    def run(
        self,
        num_iterations: Optional[int] = 500,
        alpha: float = 0.1,
        update_fragments: bool = True,
        yield_negatives: bool = False,
    ) -> Generator[FandangoInput, None, None]:
        LOGGER.debug("Starting mutation fuzzer")
        unsuccessful_tries = 0

        i = 0
        while True:
            if num_iterations is not None and i >= num_iterations:
                break

            curr_alpha = 1 - (unsuccessful_tries / (i + 1))
            if curr_alpha < alpha:
                if i > (num_iterations or 500):
                    break

            inp = self.fuzz()

            if self.process_new_input(inp, update_fragments=update_fragments):
                yield inp
            else:
                unsuccessful_tries += 1
                if yield_negatives:
                    yield inp
                # print(f"current alpha: {curr_alpha}, threshold: {alpha}")

            i += 1

    def process_new_input(self, inp: FandangoInput, update_fragments: bool) -> bool:
        if inp in self.population:
            return False

        if self.oracle is not None:
            if self.oracle(inp) == OracleResult.PASSING:
                return False

        self.population.add(inp)

        if update_fragments:
            self.update_fragments(inp)

        return True
