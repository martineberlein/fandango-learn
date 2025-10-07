import unittest

from fandango.language.parse import parse
from fandango.language.symbol import NonTerminal

from fdlearn.resources.patterns import Pattern
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.data.input import FandangoInput
from fdlearn.learning.rule_induction.rule_induction import RuleInductionLearner

from .utils import RESOURCES_ROOT


class TestLearner(unittest.TestCase):

    def test_learner_calculator_int_pattern(self):
        with open(RESOURCES_ROOT / "calculator.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        valid_inputs = {
            FandangoInput.from_str(grammar, "sqrt(-12)", True),
            FandangoInput.from_str(grammar, "sqrt(-900)", True),
            FandangoInput.from_str(grammar, "sqrt(-1)", True),
            FandangoInput.from_str(grammar, "sqrt(-11234)", True),
            FandangoInput.from_str(grammar, "sqrt(1)", False),
            FandangoInput.from_str(grammar, "sqrt(0)", False),
            FandangoInput.from_str(grammar, "sqrt(12)", False),
            FandangoInput.from_str(grammar, "cos(-12)", False),
        }

        relevant_non_terminal = {
            NonTerminal("<number>"),
            NonTerminal("<maybeminus>"),
            NonTerminal("<function>"),
        }

        learner = RuleInductionLearner(
            grammar,
        )

        invariant = learner.learn_constraints(
            valid_inputs, relevant_non_terminals=relevant_non_terminal
        )

        print(invariant)

        # for expected_constraint in expected_constraints:
        #     self.assertIn(expected_constraint, invariants)
