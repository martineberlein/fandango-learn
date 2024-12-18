import unittest
from enum import Enum
from fandango.language.symbol import NonTerminal
from fandangoLearner.resources.placeholders import Placeholder, PlaceholderType


class TestPlaceholder(unittest.TestCase):
    def test_placeholder_initialization(self):
        placeholder = Placeholder(PlaceholderType.Int)
        self.assertEqual(placeholder.ph_type, PlaceholderType.Int)
        self.assertEqual(placeholder.symbol, "<pl_int>")
        self.assertTrue(placeholder.is_non_terminal)
        self.assertFalse(placeholder.is_terminal)

    def test_placeholder_repr(self):
        placeholder = Placeholder(PlaceholderType.String)
        self.assertEqual(repr(placeholder), "Placeholder(string)")

    def test_placeholder_factory_methods(self):
        non_terminal = Placeholder.non_terminal()
        self.assertEqual(non_terminal.ph_type, PlaceholderType.NonTerminal)
        self.assertEqual(non_terminal.symbol, "<pl_NonTerminal>")

        int_placeholder = Placeholder.int()
        self.assertEqual(int_placeholder.ph_type, PlaceholderType.Int)
        self.assertEqual(int_placeholder.symbol, "<pl_int>")

        string_placeholder = Placeholder.string()
        self.assertEqual(string_placeholder.ph_type, PlaceholderType.String)
        self.assertEqual(string_placeholder.symbol, "<pl_string>")

    def test_placeholder_equality(self):
        placeholder1 = Placeholder(PlaceholderType.Int)
        placeholder2 = Placeholder(PlaceholderType.Int)
        placeholder3 = Placeholder(PlaceholderType.String)

        self.assertEqual(placeholder1, placeholder2)
        self.assertNotEqual(placeholder1, placeholder3)

    def test_placeholder_hash(self):
        placeholder1 = Placeholder(PlaceholderType.Int)
        placeholder2 = Placeholder(PlaceholderType.Int)
        placeholder3 = Placeholder(PlaceholderType.String)

        self.assertEqual(hash(placeholder1), hash(placeholder2))
        self.assertNotEqual(hash(placeholder1), hash(placeholder3))

    def test_invalid_placeholder_type(self):
        with self.assertRaises(ValueError):
            Placeholder("InvalidType")

    def test_placeholder_in_set(self):
        placeholder1 = Placeholder(PlaceholderType.Int)
        placeholder2 = Placeholder(PlaceholderType.String)
        placeholder_set = {placeholder1, placeholder2}

        self.assertIn(placeholder1, placeholder_set)
        self.assertIn(placeholder2, placeholder_set)
        self.assertEqual(len(placeholder_set), 2)


if __name__ == "__main__":
    unittest.main()
