import unittest
import os

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.refinement.generator import (
    FandangoGenerator,
    FandangoGrammarGenerator,
)


class TestInputGenerator(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        self.grammar, self.constraints = parse(filename)

    def test_fandango_generator(self):
        generator = FandangoGenerator(self.grammar)

        candidate = FandangoConstraintCandidate(self.constraints[0])
        test_inputs = generator.generate_test_inputs(candidate, 10)

        self.assertTrue(len(test_inputs) >= 10)
        self.assertTrue(all(isinstance(inp, FandangoInput) for inp in test_inputs))

        for constraint in self.constraints:
            for inp in test_inputs:
                self.assertTrue(constraint.check(inp.tree))

    def test_fandango_grammar_generator(self):
        generator = FandangoGrammarGenerator(self.grammar)

        candidate = FandangoConstraintCandidate(self.constraints[0])
        test_inputs = generator.generate_test_inputs(candidate, 10)

        self.assertTrue(len(test_inputs) == 10)
        self.assertTrue(all(isinstance(inp, FandangoInput) for inp in test_inputs))


if __name__ == "__main__":
    unittest.main()
