import unittest
from typing import Optional

from fandango.language.parse import parse

from fdlearn.resources.patterns import Pattern
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.data.input import FandangoInput
from fdlearn.learner import FandangoLearner


from .utils import RESOURCES_ROOT


class TestLearner(unittest.TestCase):

    @staticmethod
    def learn_invariants(
        grammar, patterns, valid_inputs
    ) -> Optional[set[FandangoConstraintCandidate]]:
        fdlearn = FandangoLearner(
            grammar=grammar,
            patterns=patterns,
        )
        invariants = fdlearn.learn_constraints(test_inputs=valid_inputs)
        return invariants

    def test_learner_calculator_int_pattern(self):
        with open(RESOURCES_ROOT / "calculator.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        pattern = [
            Pattern(
                string_pattern="where str(<NON_TERMINAL>) == <STRING>",
            ),
            Pattern(
                string_pattern="where int(<NON_TERMINAL>) <= <INTEGER>",
            ),
        ]

        valid_inputs = {
            FandangoInput.from_str(grammar, "sqrt(-12)", True),
            FandangoInput.from_str(grammar, "sqrt(-900)", True),
            FandangoInput.from_str(grammar, "sqrt(12)", False),
            FandangoInput.from_str(grammar, "cos(-12)", False),
        }

        invariants = self.learn_invariants(grammar, pattern, valid_inputs)

        expected_constraints = [
            FandangoConstraintCandidate.from_str(
                """where int(<number>) <= -12 and str(<function>) == 'sqrt'"""
            ),
            FandangoConstraintCandidate.from_str(
                """where str(<function>) == 'sqrt' and str(<maybeminus>) == '-'"""
            ),
        ]
        for expected_constraint in expected_constraints:
            self.assertIn(expected_constraint, invariants)

    def test_learner_xml(self):
        with open(RESOURCES_ROOT / "xml.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        pattern = [
            Pattern(
                string_pattern="where forall <elem> in <NON_TERMINAL>: str(<ATTRIBUTE>) == str(<ATTRIBUTE>)",
            )
        ]

        valid_inputs = {
            FandangoInput.from_str(grammar, "<h1><text>test</text></h1>", True),
            FandangoInput.from_str(grammar, "<p>abc</p>", True),
            FandangoInput.from_str(grammar, "<b/>", True),
            FandangoInput.from_str(grammar, "<p>abc</a>", False),
        }

        fdlearn = FandangoLearner(
            grammar=grammar,
            patterns=pattern,
        )

        invariants = fdlearn.learn_constraints(test_inputs=valid_inputs)
        self.assertEqual(len(invariants), 2)

        expected_constraint = FandangoConstraintCandidate.from_str(
            """where forall <elem> in <xml_tree>: str(<elem>.<xml_close_tag>.<id>) ==str(<elem>.<xml_open_tag>.<id>)"""
        )
        self.assertIn(expected_constraint, invariants)
        self.assertIn(expected_constraint, fdlearn.get_best_candidates())


if __name__ == "__main__":
    unittest.main()
