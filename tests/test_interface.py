import unittest
import os

from fandango.language.grammar import Grammar
from fandango.constraints.base import Constraint

from fdlearn.interface.fandango import parse, parse_constraint, parse_contents


class InterfaceTest(unittest.TestCase):

    GRAMMAR = """
    <start> ::= <ab>;
    <ab> ::= 
          "a" <ab> 
        | <ab> "b"
        | ""
        ;
    """

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
        grammar, constraints = parse_contents(self.GRAMMAR + "str(<ab>) == 'a';")
        self.assertIsInstance(grammar, Grammar)

        self.assertIsNotNone(constraints)
        self.assertEqual(len(constraints), 1)
        self.assertIsInstance(constraints[0], Constraint)

    def test_parse_constraint(self):
        """
        Test the parse_constraint function.
        """
        constraint = parse_constraint("str(<ab>) == 'a';")
        self.assertIsInstance(constraint, Constraint)

    def test_parse_constraint_none(self):
        """
        Test the check function with a constraint that compares None values.
        This should return False. If this tests fails, it means that the fandango check function is broken.
        See fandango issue #346.
        """
        constraint = parse_constraint("int(<start>) == int(<ab>);")
        self.assertIsInstance(constraint, Constraint)

        grammar, _ = parse_contents(self.GRAMMAR)
        tree = grammar.parse("a")
        self.assertIsNotNone(tree)
        self.assertFalse(constraint.check(tree))


if __name__ == "__main__":
    unittest.main()
