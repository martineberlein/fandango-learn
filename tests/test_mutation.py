import unittest
import os
import random

from fandango.language.symbol import NonTerminal
from fandango.language.tree import DerivationTree

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.interface.fandango import parse_file
from fdlearn.refinement.mutation import (
    get_paths,
    get_subtree,
    MutationFuzzer,
    replace_subtree,
    ReplaceRandomSubtreeOperator,
    SwapSubtreeOperator,
)


class TestMutationFuzzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_path = os.path.dirname(__file__)
        file = os.path.join(cls.base_path, "resources", "calculator.fan")
        cls.grammar, _ = parse_file(file)

    def setUp(self):

        test_inputs = [
            ("sqrt(-1)", True),
            ("sqrt(-10)", True),
            ("sqrt(-900)", True),
            ("sqrt(3)", False),
            ("cos(3)", False),
            ("sin(-1)", False),
        ]
        self.test_inputs = [
            FandangoInput.from_str(self.grammar, inp, res) for inp, res in test_inputs
        ]
        random.seed(0)

    def test_paths_traversal(self):
        inp = self.test_inputs[-1]

        result = get_paths(inp.tree)
        self.assertGreater(
            len(result), 0, "get_paths() should return at least one path."
        )

        ps = [
            path for path, subtree in result if isinstance(subtree.symbol, NonTerminal)
        ]
        self.assertGreater(
            len(ps), 0, "There should be at least one non-terminal path."
        )

        subtree = get_subtree(inp.tree, ps[0])
        self.assertIsNotNone(subtree, "Subtree should not be None.")
        self.assertIsInstance(
            subtree, DerivationTree, "Expected subtree to be a DerivationTree."
        )

    def test_mutation_fuzzer_instantiation(self):
        mutation_fuzzer = MutationFuzzer(self.grammar, self.test_inputs, None)
        self.assertIsInstance(mutation_fuzzer, MutationFuzzer)
        self.assertGreaterEqual(len(mutation_fuzzer.population), len(self.test_inputs))

    def test_replace_sub_tree(self):
        inp = self.test_inputs[-1]
        ps = [
            path
            for path, subtree in get_paths(inp.tree)
            if isinstance(subtree.symbol, NonTerminal)
        ]
        self.assertGreater(len(ps), 0, "No valid non-terminal paths found.")

        inp_ = self.test_inputs[-2]
        subtree = get_subtree(inp_.tree, ps[0])

        new_tree = replace_subtree(inp.tree, ps[0], subtree)
        self.assertIsNotNone(new_tree)
        self.assertIsInstance(new_tree, DerivationTree)

    def test_subtree_fuzzer(self):
        test_inputs = [self.grammar.fuzz("<number>") for _ in range(10)]
        self.assertGreater(
            len(test_inputs), 0, "Fuzzer should generate non-empty inputs."
        )
        for inp in test_inputs:
            self.assertIsInstance(inp, DerivationTree)

    def test_random_subtree_mutator(self):
        mutator = ReplaceRandomSubtreeOperator(self.grammar)
        inp = self.test_inputs[0]
        all_paths = [
            path
            for path, subtree in get_paths(inp.tree)
            if isinstance(subtree.symbol, NonTerminal)
        ]
        self.assertGreater(len(all_paths), 0, "No valid non-terminal paths found.")

        new_tree = mutator.replace(inp.tree, all_paths[3])
        self.assertIsNotNone(new_tree, "Mutation should produce a new tree.")
        self.assertIsInstance(new_tree, DerivationTree)

    def test_swap_subtree_mutator(self):
        mutator = SwapSubtreeOperator()
        inp = FandangoInput.from_str(self.grammar, "sqrt(123)")
        all_paths = [
            path
            for path, subtree in get_paths(inp.tree)
            if isinstance(subtree.symbol, NonTerminal)
        ]
        self.assertGreater(len(all_paths), 0, "No valid non-terminal paths found.")

        new_tree = mutator.replace(inp.tree, all_paths[9])
        self.assertIsNotNone(new_tree, "Swap mutation should produce a new tree.")
        self.assertIsInstance(new_tree, DerivationTree)

    def test_mutation_fuzzer_mutate(self):
        mutation_fuzzer = MutationFuzzer(self.grammar, self.test_inputs, None)
        inp = FandangoInput.from_str(self.grammar, "sqrt(-123)")

        mutated_inputs = [mutation_fuzzer.mutate(inp) for _ in range(10)]
        self.assertTrue(any(mutated_inputs), "At least one mutation should succeed.")

    def test_mutation_fuzzer_run(self):
        positive_input = FandangoInput.from_str(self.grammar, "sqrt(-12)")

        def oracle(inp_: FandangoInput):
            t = inp_.tree
            num_t = t.find_all_trees(NonTerminal("<number>"))[0]
            return (
                OracleResult.FAILING
                if -20 < int(str(num_t)) <= -1
                else OracleResult.PASSING
            )

        mutation_fuzzer = MutationFuzzer(self.grammar, [positive_input], oracle)
        generator = mutation_fuzzer.run()

        results = []
        for inp in list(generator):
            print(inp)
            results.append(inp)
        self.assertGreater(
            len(results), 0, "Mutation fuzzer should generate at least one output."
        )
        self.assertTrue(
            all(isinstance(inp, FandangoInput) for inp in results),
            "All outputs should be FandangoInput instances.",
        )


if __name__ == "__main__":
    unittest.main()
