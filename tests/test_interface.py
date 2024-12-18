import unittest

from fandango.language.grammar import Grammar
from fandango.constraints.base import Constraint

from fandangoLearner.interface.fandango import parse, parse_constraint


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
        grammar, constraints = parse(self.GRAMMAR + "str(<ab>) == 'a';")
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


if __name__ == "__main__":
    unittest.main()
