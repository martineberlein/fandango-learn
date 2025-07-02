import unittest
import random

from fandango.language.parse import parse
from fandango.constraints.base import (
    ComparisonConstraint,
    ConjunctionConstraint,
    ExistsConstraint,
    ForallConstraint,
    ExpressionConstraint,
    DisjunctionConstraint,
)
from fandango.language.search import RuleSearch, AttributeSearch, LengthSearch

from fdlearn.data import FandangoInput
from fdlearn.interface import parse_constraint
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.learning.instantiation import (
    NonTerminalPlaceholderTransformer,
    ValueMap,
    PatternProcessor,
)
from fdlearn.learning.value_map import get_reachability_map_level, ReachabilityMap
from fdlearn.reduction.feature_class import get_direct_reachability_map
from fdlearn.learning.value_transformer import (
    IntegerPlaceholderTransformer,
    StringPlaceholderTransformer,
)
from fdlearn.resources import Pattern

from .utils import RESOURCES_ROOT, PlaceholderVisitor


class TestPatternInstantiation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        random.seed(42)
        with open(RESOURCES_ROOT / "calculator.fan", "r") as f:
            cls.grammar, _ = parse(f, use_cache=False, use_stdlib=False)

        relevant_non_terminals = set(cls.grammar.rules.keys())
        reachability_map = ReachabilityMap(cls.grammar)
        cls.non_terminal_transformer = NonTerminalPlaceholderTransformer(
            relevant_non_terminals,
            reachability_map=reachability_map,
            limit_descendant_levels=2,
        )

        cls.test_inputs = set()
        for _ in range(100):
            tree = cls.grammar.fuzz()
            cls.test_inputs.add(FandangoInput(tree=tree))

        cls.value_map = ValueMap.from_inputs(
            relevant_non_terminals=relevant_non_terminals, inputs=cls.test_inputs
        )
        cls.integer_transformer = IntegerPlaceholderTransformer(
            value_map=cls.value_map,
            test_inputs=cls.test_inputs,
        )
        cls.string_transformer = StringPlaceholderTransformer(
            value_map=cls.value_map,
            test_inputs=cls.test_inputs,
        )
        cls.placeholder_visitor = PlaceholderVisitor()

    def transform_pattern(self, pattern):
        transformed_patterns = self.non_terminal_transformer.transform(pattern)
        self.assertTrue(all(isinstance(p, type(pattern)) for p in transformed_patterns))
        self.assertFalse(
            any(self.placeholder_visitor.visit(p) for p in transformed_patterns)
        )
        return transformed_patterns

    def test_non_terminal_transformer_1(self):
        pattern = parse_constraint("where int(<NON_TERMINAL>) <= -1")
        transformed_patterns = self.transform_pattern(pattern)

        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_non_terminal_transformer_2(self):
        pattern = parse_constraint("where int(<elem>) <= -1")
        transformed_patterns = self.transform_pattern(pattern)

        self.assertEqual(len(transformed_patterns), 1)

        unchanged_pattern = transformed_patterns[0]
        self.assertEqual(str(unchanged_pattern), str(pattern))
        # self.assertEqual(unchanged_pattern.searches, pattern.searches)

    def test_non_terminal_transformer_3(self):
        pattern = parse_constraint(
            "where int(<NON_TERMINAL>) <= -1 and str(<NON_TERMINAL>) == 'a'"
        )
        self.assertIsInstance(pattern, ConjunctionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules) ** 2)

    def test_non_terminal_transformer_3_0(self):
        pattern = parse_constraint(
            "where int(<NON_TERMINAL>) <= -1 or str(<NON_TERMINAL>) == 'a'"
        )
        self.assertIsInstance(pattern, DisjunctionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules) ** 2)

    def test_non_terminal_transformer_3_1(self):
        pattern = parse_constraint(
            "where (int(<NON_TERMINAL>) + str(<NON_TERMINAL>)) == 0"
        )
        self.assertIsInstance(pattern, ComparisonConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules) ** 2)

    def test_non_terminal_transformer_3_2(self):
        pattern = parse_constraint("where str(<NON_TERMINAL>) in 'sqrt'")
        self.assertIsInstance(pattern, ExpressionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_non_terminal_transformer_4(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<elem>) <= -1"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.statement, ComparisonConstraint)

    def test_non_terminal_transformer_5(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<elem>) <= -1 and str(<elem>) == 'a'"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.statement, ConjunctionConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))

    def test_non_terminal_transformer_6(self):
        pattern = parse_constraint(
            "where forall <elem> in <NON_TERMINAL>: int(<elem>) <= -1 and str(<NON_TERMINAL>) == 'a'"
        )
        self.assertIsInstance(pattern, ForallConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules) ** 2)

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ForallConstraint)
            self.assertIsInstance(pattern.statement, ConjunctionConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))

    def test_non_terminal_transformer_7(self):
        pattern = parse_constraint("where 'abc' in str(<NON_TERMINAL>)")
        self.assertIsInstance(pattern, ExpressionConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_non_terminal_transformer_8(self):
        pattern = parse_constraint(
            "where exists <elem> in <NON_TERMINAL>: int(<ATTRIBUTE>) <= 1"
        )
        self.assertIsInstance(pattern, ExistsConstraint)

        transformed_patterns = self.transform_pattern(pattern)
        for p in transformed_patterns:
            print(p)
        self.assertEqual(len(transformed_patterns), 15)

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ExistsConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))
            bounded_constraint = pattern.statement
            self.assertIsInstance(bounded_constraint, ComparisonConstraint)
            self.assertTrue(
                all(
                    isinstance(att, AttributeSearch)
                    for att in list(bounded_constraint.searches.values())
                )
            )

    def test_non_terminal_transformer_9(self):
        pattern = parse_constraint(
            "where forall <elem> in <NON_TERMINAL>: int(<ATTRIBUTE>) <= 1"
        )
        self.assertIsInstance(pattern, ForallConstraint)
        transformed_patterns = self.transform_pattern(pattern)
        self.assertEqual(len(transformed_patterns), 15)

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ForallConstraint)
            self.assertIsInstance(pattern.search, RuleSearch)
            self.assertTrue(pattern.search.symbol in list(self.grammar.rules.keys()))
            bounded_constraint = pattern.statement
            self.assertIsInstance(bounded_constraint, ComparisonConstraint)
            self.assertTrue(
                all(
                    isinstance(att, AttributeSearch)
                    for att in list(bounded_constraint.searches.values())
                )
            )

    def test_integer_transformer_10(self):
        pattern = parse_constraint("where int(<number>) <= <INTEGER>")
        transformed_patterns = self.integer_transformer.transform(pattern)
        for p in transformed_patterns:
            print(p)
        self.assertTrue(
            all(isinstance(p, ComparisonConstraint) for p in transformed_patterns)
        )
        self.assertEqual(len(transformed_patterns), 2)

    def test_integer_transformer_11(self):
        pattern = parse_constraint(
            "where int(<number>) <= <INTEGER> and int(<number>) <= <INTEGER>"
        )
        transformed_patterns = self.integer_transformer.transform(pattern)
        self.assertTrue(
            all(isinstance(p, ConjunctionConstraint) for p in transformed_patterns)
        )
        self.assertEqual(len(transformed_patterns), 4)

    def test_integer_transformer_12(self):
        pattern = parse_constraint("where int(<number>) <= <INTEGER>")
        integer_transformer = IntegerPlaceholderTransformer(
            value_map=self.value_map,
            test_inputs=self.test_inputs,
            use_partial_evaluation=True,
        )
        transformed_patterns = integer_transformer.transform(pattern)
        for p in transformed_patterns:
            print(p)
        self.assertTrue(
            all(isinstance(p, ComparisonConstraint) for p in transformed_patterns)
        )
        self.assertEqual(len(transformed_patterns), 59)

    def test_non_terminal_transformer_length_1(self):
        pattern = parse_constraint(
            "where forall <elem> in <NON_TERMINAL>: len(*<ATTRIBUTE>) <= 10"
        )
        transformed_patterns = self.non_terminal_transformer.transform(pattern)
        for p in transformed_patterns:
            print(p)

        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

        for pattern in transformed_patterns:
            self.assertIsInstance(pattern, ForallConstraint)
            self.assertIsInstance(pattern.statement, ComparisonConstraint)
            self.assertTrue(
                all(
                    isinstance(att, LengthSearch)
                    for att in list(pattern.statement.searches.values())
                )
            )

    def test_non_terminal_transformer_length_2(self):
        pattern = parse_constraint("where len(*<NON_TERMINAL>) <= 10")
        transformed_patterns = self.non_terminal_transformer.transform(pattern)
        for p in transformed_patterns:
            print(p)

        self.assertEqual(len(transformed_patterns), len(self.grammar.rules))

    def test_pattern_processor_xml(self):
        with open(RESOURCES_ROOT / "xml.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        pattern = [
            Pattern(
                string_pattern="where forall <elem> in <NON_TERMINAL>: str(<ATTRIBUTE>) == str(<ATTRIBUTE>)",
            ).instantiated_pattern
        ]
        pattern_processor = PatternProcessor(
            pattern,
        )

        valid_inputs = {
            FandangoInput.from_str(grammar, "<h1><text>test</text></h1>", True),
            FandangoInput.from_str(grammar, "<p>abc</p>", True),
            FandangoInput.from_str(grammar, "<b/>", True),
        }

        relevant_non_terminals = set(grammar.rules.keys())
        reachability_map = ReachabilityMap(grammar)
        value_map = ValueMap.from_inputs(relevant_non_terminals, valid_inputs)
        atomic_constraints = pattern_processor.instantiate_patterns(
            relevant_non_terminals, valid_inputs, value_map, reachability_map
        )
        self.assertFalse(
            any(
                self.placeholder_visitor.visit(p.constraint) for p in atomic_constraints
            )
        )

        expected_constraint = parse_constraint(
            """where forall <elem> in <xml_tree>: str(<elem>.<xml_close_tag>.<id>) ==str(<elem>.<xml_open_tag>.<id>)"""
        )
        expected_constraint = FandangoConstraintCandidate(expected_constraint)

        self.assertIn(expected_constraint, atomic_constraints)

    def test_integer_transformer_15(self):
        pattern = parse_constraint("where <STRING> in str(<function>) ")
        transformed_patterns = self.string_transformer.transform(pattern)
        self.assertEqual(len(transformed_patterns), 4)
        self.assertTrue(
            all(isinstance(p, ExpressionConstraint) for p in transformed_patterns)
        )
        self.assertFalse(
            any(self.placeholder_visitor.visit(p) for p in transformed_patterns)
        )


if __name__ == "__main__":
    unittest.main()
