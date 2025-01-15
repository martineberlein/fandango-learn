import unittest
from pathlib import Path

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse_file
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.refinement.generator import FandangoGenerator


class TestInputGenerator(unittest.TestCase):

    def setUp(self):
        file = Path("tests/resources/calculator.fan")
        self.grammar, self.constraints = parse_file(file)

    def test_fandango_fuzzer(self):
        generator = FandangoGenerator(self.grammar)

        candidate = FandangoConstraintCandidate(self.constraints[0])
        test_inputs = generator.generate_test_inputs(candidate)

        self.assertTrue(len(test_inputs) >= 10)
        self.assertTrue(all(isinstance(inp, FandangoInput) for inp in test_inputs))

        for constraint in self.constraints:
            for inp in test_inputs:
                self.assertTrue(constraint.check(inp.tree))


if __name__ == "__main__":
    unittest.main()
