import unittest
import os

from fandango.evolution.algorithm import Fandango
from fandango.language.grammar import Grammar
from fandango.constraints.base import (
    Constraint,
    ExistsConstraint,
    ConjunctionConstraint,
    ComparisonConstraint,
)

from fdlearn.interface.fandango import parse, parse_constraint, parse_contents
from .utils import RESOURCES_ROOT


class InterfaceTest(unittest.TestCase):

    GRAMMAR = """
<start> ::= <ab>;
<ab> ::= "a" <ab> | <ab> "b"| "" ;"""

    def test_parse(self):
        """
        Test the parse function.
        """
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        grammar, constraints = parse(filename)
        self.assertIsInstance(grammar, Grammar)

        self.assertIsNotNone(constraints)
        self.assertEqual(len(constraints), 1)
        self.assertIsInstance(constraints[0], Constraint)

    def test_parse_contents(self):
        """
        Test the parse contents function.
        """
        grammar, constraints = parse_contents(self.GRAMMAR + "where str(<ab>) == 'a'")
        self.assertIsInstance(grammar, Grammar)

        self.assertIsNotNone(constraints)
        self.assertEqual(len(constraints), 1)
        self.assertIsInstance(constraints[0], Constraint)

    def test_parse_constraint(self):
        """
        Test the parse_constraint function.
        """
        constraint = parse_constraint("where str(<ab>) == 'a'")
        self.assertIsInstance(constraint, Constraint)

    def test_parse_constraint_none(self):
        """
        Test the check function with a constraint that compares None values.
        This should return False. If this tests fails, it means that the fandango check function is broken.
        See fandango issue #346.
        """
        constraint = parse_constraint("where int(<start>) == int(<ab>)")
        self.assertIsInstance(constraint, Constraint)

        grammar, _ = parse_contents(self.GRAMMAR)
        tree = grammar.parse("a")
        self.assertIsNotNone(tree)
        self.assertFalse(constraint.check(tree))

    def test_fandango_fuzzer(self):
        """
        Test the fandango fuzzer.
        """
        grammar, _ = parse_contents(self.GRAMMAR)
        constraint = parse_constraint("where len(<start>) > 0")
        self.assertIsInstance(grammar, Grammar)
        solutions = []

        fandango = Fandango(grammar, [constraint])
        fan_gen = fandango.generate()

        for solution in fan_gen:
            solutions.append(str(solution))
            if len(solutions) == 2:
                break

        self.assertEqual(len(solutions), 2)

    @unittest.skip(
        "Skipping test_fandango_parser_conjunction_constraint due to complexity"
    )
    def test_fandango_parser_conjunction_constraint(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: (int(<elem>) <= -1 and str(<elem>) == 'a')"
        )
        self.assertIsInstance(pattern, ExistsConstraint)
        self.assertIsInstance(pattern.statement, ComparisonConstraint)

    def test_fandango_parser_constraints(self):
        from fandango.language.parse import parse

        with open(RESOURCES_ROOT / "calculator.fan", "r") as f:
            grammar, constraints = parse(f, use_cache=False, use_stdlib=False)

        solutions = set()

        fandango = Fandango(grammar, constraints)
        fandango_generator = fandango.generate()

        for inp in fandango_generator:
            solutions.add(inp)
            if len(solutions) >= 10:
                break
        self.assertEqual(len(solutions), 10)


if __name__ == "__main__":
    unittest.main()
