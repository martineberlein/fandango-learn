import unittest

from fdlearn.interface import parse, parse_contents, parse_constraint
from fdlearn.resources import Pattern


class TestPatternsWithPlaceholders(unittest.TestCase):

    def test_exists_pattern(self):
        """
        Test Pattern with exists placeholder
        """
        pattern = Pattern(
            string_pattern=f"exists <container> in <NON_TERMINAL>: int(<container>) <= 5;"
        )
        print(type(pattern.instantiated_pattern))

    def test_inside_constraint(self):
        """
        Test Pattern with inside placeholder
        """
        grammar = """
        <start> ::= <A> | <B>;
        <A> ::= "a";
        <B> ::= "b";
        """
        grammar, _ = parse_contents(grammar)

        inp1 = grammar.parse("a")
        inp2 = grammar.parse("b")

        constraint = parse_constraint(
            "exists <elem> in <A>: is_inside(<elem>, <start>);"
        )
        print(constraint)
        self.assertTrue(constraint.check(inp1))
        self.assertFalse(constraint.check(inp2))

    def test_inside_pattern(self):
        grammar = """
        <start> ::= <A> | <B>;
        <A> ::= "a";
        <B> ::= "b";
        """
        grammar, _ = parse_contents(grammar)

        inp1 = grammar.parse("a")
        inp2 = grammar.parse("b")

        pattern = Pattern(
            string_pattern="exists <elem> in <A>: is_inside(<elem>, <start>);",
        )
        constraint = pattern.instantiated_pattern
        print(constraint.check(inp1))
        print(constraint.check(inp2))
        self.assertTrue(constraint.check(inp1))
        self.assertFalse(constraint.check(inp2))

    def test_contains_pattern(self):
        grammar = """
        <start> ::= <string>;
        <string> ::= <char>+;
        <char> ::= <A> | <B>;
        <A> ::= "a";
        <B> ::= "b";
        """
        grammar, _ = parse_contents(grammar)

        inp1 = grammar.parse("a")
        # print('a' in str(inp1))
        inp2 = grammar.parse("b")
        # print('bb' in str(inp2))
        inp3 = grammar.parse("bbb")
        # print('bb' in str(inp3))

        pattern = Pattern(
            string_pattern="exists <elem> in <start>: str_contains(<elem>, 'bb');",
            use_cache=False,
        )
        constraint = pattern.instantiated_pattern
        self.assertFalse(constraint.check(inp1))
        self.assertFalse(constraint.check(inp2))
        self.assertTrue(constraint.check(inp3))

    def test_contains_escaped_pattern(self):
        grammar = r"""
        <start> ::= <string>;
        <string> ::= <char>+;
        <char> ::= <A> | <B> | <newline>;
        <A> ::= "a";
        <B> ::= "b";
        <newline> ::= "\\n";
        """
        grammar, _ = parse_contents(grammar)

        inp1 = grammar.parse("a")
        inp2 = grammar.parse("b")
        inp3 = grammar.parse("bbb\\n\\n")
        inp4 = grammar.parse("\\n\\nb")
        inp5 = grammar.parse("\\n\\n")

        pattern = Pattern(
            string_pattern=r"exists <elem> in <string>: str_contains(<elem>, '\\n\\n');",
            use_cache=False,
        )

        constraint = pattern.instantiated_pattern
        print(constraint)
        self.assertFalse(constraint.check(inp1))
        self.assertFalse(constraint.check(inp2))
        self.assertTrue(constraint.check(inp3))
        self.assertTrue(constraint.check(inp4))
        self.assertFalse(constraint.check(inp5))

    @unittest.skip
    def test_parsing_constraint_grep(self):
        from dbgbench.resources import get_grep_grammar_path

        grammar, _ = parse(get_grep_grammar_path())

        benign = "printf 'haha\\n' | LC_ALL=tr_TR.utf8 timeout 0.5s grep -i 'ha'"

        escp = "a\\\\n"
        pattern = Pattern(
            string_pattern=f"exists <elem> in <input_>: str_contains(<elem>, '{escp}');",
            use_cache=False,
        )
        constraint = pattern.instantiated_pattern
        self.assertTrue(constraint.check(grammar.parse(benign)))


if __name__ == "__main__":
    unittest.main()
