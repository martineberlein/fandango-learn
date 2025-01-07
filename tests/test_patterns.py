import unittest
from fandangoLearner.resources.patterns import Pattern
from fandangoLearner.resources.placeholders import Placeholder, PlaceholderType


class TestPatternsWithPlaceholders(unittest.TestCase):
    def test_non_terminal_placeholder(self):
        """
        Test Pattern with NonTerminal placeholder
        """
        non_terminal_placeholder = Placeholder.non_terminal()
        pattern = Pattern(
            string_pattern=f"str({non_terminal_placeholder}) == 'test';"
        )
        self.assertEqual(pattern.string_pattern, "str(<pl_NonTerminal>) == 'test';")
        self.assertTrue(isinstance(non_terminal_placeholder, Placeholder))
        self.assertEqual(non_terminal_placeholder.ph_type, PlaceholderType.NonTerminal)

    def test_int_placeholder(self):
        """
        Test Pattern with int placeholder
        """
        int_placeholder = Placeholder.int()
        pattern = Pattern(
            string_pattern=f"int({int_placeholder}) > 5;"
        )
        self.assertEqual(pattern.string_pattern, "int(<pl_int>) > 5;")
        self.assertTrue(isinstance(int_placeholder, Placeholder))
        self.assertEqual(int_placeholder.ph_type, PlaceholderType.Int)

    def test_string_placeholder(self):
        """
        Test Pattern with string placeholder
        """
        string_placeholder = Placeholder.string()
        pattern = Pattern(
            string_pattern=f"str({string_placeholder}) == 'hello';"
        )
        self.assertEqual(pattern.string_pattern, "str(<pl_string>) == 'hello';")
        self.assertTrue(isinstance(string_placeholder, Placeholder))
        self.assertEqual(string_placeholder.ph_type, PlaceholderType.String)

    def test_combined_placeholders(self):
        """
        Test Pattern with multiple types of placeholders combined
        """
        non_terminal = Placeholder.non_terminal()
        int_placeholder = Placeholder.int()
        string_placeholder = Placeholder.string()

        pattern = Pattern(
            string_pattern=f"int({int_placeholder}) == len(str({string_placeholder})) + 2 * int({non_terminal});"
        )

        self.assertEqual(
            pattern.string_pattern,
            "int(<pl_int>) == len(str(<pl_string>)) + 2 * int(<pl_NonTerminal>);"
        )

    def test_invalid_placeholder_type(self):
        """
        Ensure invalid placeholder types raise ValueError
        """
        with self.assertRaises(ValueError):
            Placeholder("invalid_type")  # This should raise an exception


if __name__ == "__main__":
    unittest.main()