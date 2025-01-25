import unittest
import os

from fandango.constraints.base import ConjunctionConstraint

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse, parse_constraint
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.refinement.negation import construct_negations
from fandangoLearner.refinement.generator import (
    FandangoGenerator,
    FandangoGrammarGenerator,
)


class TestInputGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        cls.grammar, cls.constraints = parse(filename)
        cls.generator = FandangoGenerator(cls.grammar)
        cls.grammar_generator = FandangoGrammarGenerator(cls.grammar)

    def generate_and_test_inputs(self, candidate, expected_count):
        test_inputs = self.generator.generate_test_inputs(candidate, expected_count)
        self.assertEqual(len(test_inputs), expected_count)
        self.assertTrue(all(isinstance(inp, FandangoInput) for inp in test_inputs))
        return test_inputs

    def test_fandango_generator_with_constraints_1(self):
        candidate = FandangoConstraintCandidate(self.constraints[0])
        test_inputs = self.generate_and_test_inputs(candidate, 10)

        for constraint in self.constraints:
            with self.subTest(constraint=constraint):
                for inp in test_inputs:
                    self.assertTrue(constraint.check(inp.tree))

    def test_fandango_generator_with_constraints_2(self):
        constraint = parse_constraint("int(<number>) <= 0;")
        candidate = FandangoConstraintCandidate(constraint)
        test_inputs = self.generate_and_test_inputs(candidate, 10)

        with self.subTest(constraint=constraint):
            for inp in test_inputs:
                self.assertTrue(constraint.check(inp.tree))

    def test_fandango_generator_with_negation(self):
        constraint = parse_constraint("int(<number>) <= 0;")
        negation_candidate = -FandangoConstraintCandidate(constraint)
        test_inputs = self.generate_and_test_inputs(negation_candidate, 10)

        for inp in test_inputs:
            with self.subTest(input=inp):
                self.assertTrue(negation_candidate.constraint.check(inp.tree))

    def test_fandango_generator_with_negation_conjunction(self):
        constraint_1 = parse_constraint("int(<number>) <= 0;")
        constraint_2 = parse_constraint("str(<function>) == 'sqrt';")
        candidate_conjunction = FandangoConstraintCandidate(ConjunctionConstraint([constraint_1, constraint_2]))
        negated_candidates = construct_negations([candidate_conjunction])

        for negation_candidate in negated_candidates:
            test_inputs = self.generate_and_test_inputs(negation_candidate, 10)
            print(negation_candidate.constraint, test_inputs)
            for inp in test_inputs:
                with self.subTest(input=inp):
                    self.assertTrue(negation_candidate.constraint.check(inp.tree))

    def test_fandango_grammar_generator_basic(self):
        candidate = FandangoConstraintCandidate(self.constraints[0])
        test_inputs = self.grammar_generator.generate_test_inputs(candidate, 10)

        self.assertEqual(len(test_inputs), 10)
        self.assertTrue(all(isinstance(inp, FandangoInput) for inp in test_inputs))


if __name__ == "__main__":
    unittest.main()
