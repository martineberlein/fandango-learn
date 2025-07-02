import unittest

from fandango.language.parse import parse

from fdlearn.data.input import FandangoInput
from fdlearn.interface.fandango import parse_constraint
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.refinement.generator import FandangoGenerator
from fdlearn.refinement.engine import (
    SingleEngine,
    ParallelEngine,
)
from .utils import RESOURCES_ROOT


class TestEngine(unittest.TestCase):

    def setUp(self):
        with open(RESOURCES_ROOT / "calculator.fan", "r") as calc:
            self.grammar, self.constraints = parse(calc)

        self.candidate1 = FandangoConstraintCandidate(
            parse_constraint("where str(<function>) == 'cos'")
        )

        self.candidate2 = FandangoConstraintCandidate(
            parse_constraint("where str(<function>) == 'sqrt'")
        )

        self.fandango_generator = FandangoGenerator(self.grammar)

    def test_single_engine_generate(self):
        engine = SingleEngine(self.fandango_generator)
        candidates = [self.candidate1, self.candidate2]
        test_inputs = engine.generate(candidates)
        self.assertTrue(len(test_inputs) >= 4)
        # Check that the test_inputs contain expected patterns
        for inp in test_inputs:
            self.assertIsInstance(inp, FandangoInput)
            self.assertTrue(
                self.candidate1.constraint.check(inp.tree)
                ^ self.candidate2.constraint.check(inp.tree)
            )
        # print("SingleEngine test_inputs:", [str(inp) for inp in test_inputs])

    def test_parallel_engine_generate(self):
        engine = ParallelEngine(self.fandango_generator, workers=6)
        candidates = [self.candidate1, self.candidate2]
        test_inputs = engine.generate(candidates)
        self.assertTrue(len(test_inputs) >= 4)
        # Check that the test_inputs contain expected patterns
        for inp in test_inputs:
            self.assertIsInstance(inp, FandangoInput)
            self.assertTrue(
                self.candidate1.constraint.check(inp.tree)
                ^ self.candidate2.constraint.check(inp.tree)
            )
        # print("ParallelEngine test_inputs:", [str(inp) for inp in test_inputs])


if __name__ == "__main__":
    unittest.main()
