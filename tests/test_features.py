import unittest
import os

from fandango.language.grammar import NonTerminalNode, TerminalNode, Concatenation
from numpy import inf

from fandango.language.symbol import NonTerminal, Terminal

from fandangoLearner.interface.fandango import parse
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.reduction.feature_collector import GrammarFeatureCollector
from fandangoLearner.reduction.feature_class import (
    FeatureFactory,
    ExistenceFeature,
    DerivationFeature,
    NumericFeature,
    LengthFeature, FeatureVector,
)


class FeatureExtraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dirname = os.path.dirname(__file__)

        cls.grammar, _ = parse(os.path.join(cls.dirname, "resources", "grammar.fan"))
        cls.grammar_with_maybe_minus, _ = parse(
            os.path.join(cls.dirname, "resources", "grammar_with_minus.fan")
        )
        cls.grammar_recursion, _ = parse(
            os.path.join(cls.dirname, "resources", "grammar_recursion.fan")
        )
        cls.grammar_with_quotes, _ = parse(
            os.path.join(cls.dirname, "resources", "grammar_with_quotes.fan")
        )

    def test_build_existence_feature(self):
        expected_feature_list = [
            ExistenceFeature(NonTerminal("<start>")),
            ExistenceFeature(NonTerminal("<string>")),
            ExistenceFeature(NonTerminal("<A>")),
            ExistenceFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(self.grammar)
        features = factory.build([ExistenceFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_derivation_feature(self):
        expected_feature_list = [
            DerivationFeature(
                NonTerminal("<start>"),
                NonTerminalNode(NonTerminal("<string>")),
                grammar=self.grammar,
            ),
            DerivationFeature(
                NonTerminal("<string>"),
                NonTerminalNode(NonTerminal("<A>")),
                grammar=self.grammar,
            ),
            DerivationFeature(
                NonTerminal("<string>"),
                NonTerminalNode(NonTerminal("<B>")),
                grammar=self.grammar,
            ),
            DerivationFeature(
                NonTerminal("<string>"),
                TerminalNode(Terminal("!ab!")),
                grammar=self.grammar,
            ),
            DerivationFeature(
                NonTerminal("<A>"), TerminalNode(Terminal("a")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<A>"), TerminalNode(Terminal("b")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<A>"), TerminalNode(Terminal("c")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<A>"), TerminalNode(Terminal("d")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<A>"), TerminalNode(Terminal("e")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<B>"), TerminalNode(Terminal("0")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<B>"), TerminalNode(Terminal("1")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<B>"), TerminalNode(Terminal("2")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<B>"), TerminalNode(Terminal("3")), grammar=self.grammar
            ),
            DerivationFeature(
                NonTerminal("<B>"), TerminalNode(Terminal("4")), grammar=self.grammar
            ),
        ]
        # Concatenation([TerminalNode(Terminal('!')), TerminalNode(Terminal("a")),TerminalNode(Terminal("b")), TerminalNode(Terminal('!'))])),
        factory = FeatureFactory(self.grammar)
        features = factory.build([DerivationFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_numeric_feature(self):
        expected_feature_list = [
            NumericFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(self.grammar)
        features = factory.build([NumericFeature])

        self.assertEqual(features, expected_feature_list)

    def test_build_numeric_feature_maybe(self):
        # We do not expect num(<A>) as this is not a number
        expected_feature_list = [
            NumericFeature(NonTerminal("<start>")),
            NumericFeature(NonTerminal("<string>")),
            NumericFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(self.grammar_with_maybe_minus)
        features = factory.build([NumericFeature])

        self.assertEqual(set(features), set(expected_feature_list))

    def test_build_length_feature(self):
        expected_feature_list = [
            LengthFeature(NonTerminal("<start>")),
            LengthFeature(NonTerminal("<string>")),
            LengthFeature(NonTerminal("<A>")),
            LengthFeature(NonTerminal("<B>")),
        ]

        factory = FeatureFactory(self.grammar)
        features = factory.build([LengthFeature])

        self.assertEqual(features, expected_feature_list)

    def test_parse_existence_feature(self):
        inputs = ["4", "3", "a"]
        test_inputs = [FandangoInput.from_str(self.grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                ExistenceFeature(NonTerminal("<start>")): 1,
                ExistenceFeature(NonTerminal("<string>")): 1,
                ExistenceFeature(NonTerminal("<A>")): 0,
                ExistenceFeature(NonTerminal("<B>")): 1,
            },
            {
                ExistenceFeature(NonTerminal("<start>")): 1,
                ExistenceFeature(NonTerminal("<string>")): 1,
                ExistenceFeature(NonTerminal("<A>")): 0,
                ExistenceFeature(NonTerminal("<B>")): 1,
            },
            {
                ExistenceFeature(NonTerminal("<start>")): 1,
                ExistenceFeature(NonTerminal("<string>")): 1,
                ExistenceFeature(NonTerminal("<A>")): 1,
                ExistenceFeature(NonTerminal("<B>")): 0,
            },
        ]

        collector = GrammarFeatureCollector(self.grammar, [ExistenceFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_numeric_feature(self):
        inputs = ["4", "3", "a"]
        test_inputs = [FandangoInput.from_str(self.grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                NumericFeature(NonTerminal("<B>")): 4.0,
            },
            {
                NumericFeature(NonTerminal("<B>")): 3.0,
            },
            {
                NumericFeature(NonTerminal("<B>")): -inf,
            },
        ]

        collector = GrammarFeatureCollector(self.grammar, [NumericFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_length(self):
        inputs = ["4", "3", "a"]
        test_inputs = [FandangoInput.from_str(self.grammar, inp) for inp in inputs]

        expected_feature_vectors = [
            {
                LengthFeature(NonTerminal("<start>")): 1,
                LengthFeature(NonTerminal("<string>")): 1,
                LengthFeature(NonTerminal("<A>")): 0,
                LengthFeature(NonTerminal("<B>")): 1,
            },
            {
                LengthFeature(NonTerminal("<start>")): 1,
                LengthFeature(NonTerminal("<string>")): 1,
                LengthFeature(NonTerminal("<A>")): 0,
                LengthFeature(NonTerminal("<B>")): 1,
            },
            {
                LengthFeature(NonTerminal("<start>")): 1,
                LengthFeature(NonTerminal("<string>")): 1,
                LengthFeature(NonTerminal("<A>")): 1,
                LengthFeature(NonTerminal("<B>")): 0,
            },
        ]

        collector = GrammarFeatureCollector(self.grammar, [LengthFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_numericInterpretation_maybe_minus(self):
        inputs = ["-1", "3", "-9"]
        test_inputs = [
            FandangoInput.from_str(self.grammar_with_maybe_minus, inp) for inp in inputs
        ]

        expected_feature_vectors = [
            {
                NumericFeature(NonTerminal("<start>")): -1.0,
                NumericFeature(NonTerminal("<string>")): -1.0,
                NumericFeature(NonTerminal("<B>")): 1.0,
            },
            {
                NumericFeature(NonTerminal("<start>")): 3.0,
                NumericFeature(NonTerminal("<string>")): 3.0,
                NumericFeature(NonTerminal("<B>")): 3.0,
            },
            {
                NumericFeature(NonTerminal("<start>")): -9.0,
                NumericFeature(NonTerminal("<string>")): -9.0,
                NumericFeature(NonTerminal("<B>")): 9.0,
            },
        ]

        collector = GrammarFeatureCollector(
            self.grammar_with_maybe_minus, [NumericFeature]
        )
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_numericInterpretation_recursive(self):
        inputs = ["11923", "3341923", "9", "a"]
        test_inputs = [
            FandangoInput.from_str(self.grammar_recursion, inp) for inp in inputs
        ]

        expected_feature_vectors = [
            {
                NumericFeature(NonTerminal("<digit>")): 9.0,
                NumericFeature(NonTerminal("<B>")): 11923.0,
            },
            {
                NumericFeature(NonTerminal("<digit>")): 9.0,
                NumericFeature(NonTerminal("<B>")): 3341923.0,
            },
            {
                NumericFeature(NonTerminal("<digit>")): 9.0,
                NumericFeature(NonTerminal("<B>")): 9.0,
            },
            {
                NumericFeature(NonTerminal("<digit>")): -inf,
                NumericFeature(NonTerminal("<B>")): -inf,
            },
        ]

        collector = GrammarFeatureCollector(self.grammar_recursion, [NumericFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_parse_features_length_recursive(self):
        inputs = ["123", "ab"]
        test_inputs = [
            FandangoInput.from_str(self.grammar_recursion, inp) for inp in inputs
        ]

        expected_feature_vectors = [
            {
                LengthFeature(NonTerminal("<start>")): 3,
                LengthFeature(NonTerminal("<string>")): 3,
                LengthFeature(NonTerminal("<A>")): 0,
                LengthFeature(NonTerminal("<char>")): 0,
                LengthFeature(NonTerminal("<B>")): 3,
                LengthFeature(NonTerminal("<digit>")): 1,
            },
            {
                LengthFeature(NonTerminal("<start>")): 2,
                LengthFeature(NonTerminal("<string>")): 2,
                LengthFeature(NonTerminal("<A>")): 2,
                LengthFeature(NonTerminal("<char>")): 1,
                LengthFeature(NonTerminal("<B>")): 0,
                LengthFeature(NonTerminal("<digit>")): 0,
            },
        ]

        collector = GrammarFeatureCollector(self.grammar_recursion, [LengthFeature])
        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_build_features_with_escaped_characters(self):

        expected_feature_list = [
            DerivationFeature(
                NonTerminal("<start>"),
                NonTerminalNode(NonTerminal("<arg>")),
                grammar=self.grammar_with_quotes,
            ),
            DerivationFeature(
                NonTerminal("<arg>"),
                NonTerminalNode(NonTerminal("<digit>")),
                grammar=self.grammar_with_quotes,
            ),
            DerivationFeature(
                NonTerminal("<arg>"),
                Concatenation(
                    [
                        TerminalNode(Terminal('"')),
                        NonTerminalNode(NonTerminal("<digit>")),
                        TerminalNode(Terminal('"')),
                    ]
                ),
                grammar=self.grammar_with_quotes,
            ),
            DerivationFeature(
                NonTerminal("<digit>"),
                TerminalNode(Terminal("1")),
                grammar=self.grammar_with_quotes,
            ),
        ]

        factory = FeatureFactory(self.grammar_with_quotes)
        features = factory.build([DerivationFeature])

        self.assertEqual(set(features), set(expected_feature_list))

    def test_feature_names_with_json_chars(self):
        inputs = ["1", '"1"']
        test_inputs = [
            FandangoInput.from_str(self.grammar_with_quotes, inp) for inp in inputs
        ]

        expected_feature_vectors = [
            {
                DerivationFeature(
                    NonTerminal("<start>"),
                    NonTerminalNode(NonTerminal("<arg>")),
                    grammar=self.grammar_with_quotes,
                ): 1,
                DerivationFeature(
                    NonTerminal("<arg>"),
                    NonTerminalNode(NonTerminal("<digit>")),
                    grammar=self.grammar_with_quotes,
                ): 1,
                DerivationFeature(
                    NonTerminal("<arg>"),
                    Concatenation(
                        [
                            TerminalNode(Terminal('"')),
                            NonTerminalNode(NonTerminal("<digit>")),
                            TerminalNode(Terminal('"')),
                        ]
                    ),
                    grammar=self.grammar_with_quotes,
                ): 0,
                DerivationFeature(
                    NonTerminal("<digit>"),
                    TerminalNode(Terminal("1")),
                    grammar=self.grammar_with_quotes,
                ): 1,
            },
            {
                DerivationFeature(
                    NonTerminal("<start>"),
                    NonTerminalNode(NonTerminal("<arg>")),
                    grammar=self.grammar_with_quotes,
                ): 1,
                DerivationFeature(
                    NonTerminal("<arg>"),
                    NonTerminalNode(NonTerminal("<digit>")),
                    grammar=self.grammar_with_quotes,
                ): 0,
                DerivationFeature(
                    NonTerminal("<arg>"),
                    Concatenation(
                        [
                            TerminalNode(Terminal('"')),
                            NonTerminalNode(NonTerminal("<digit>")),
                            TerminalNode(Terminal('"')),
                        ]
                    ),
                    grammar=self.grammar_with_quotes,
                ): 1,
                DerivationFeature(
                    NonTerminal("<digit>"),
                    TerminalNode(Terminal("1")),
                    grammar=self.grammar_with_quotes,
                ): 1,
            },
        ]

        collector = GrammarFeatureCollector(
            self.grammar_with_quotes, [DerivationFeature]
        )

        for test_input, expected_feature_vectors in zip(
            test_inputs, expected_feature_vectors
        ):
            feature_vector = collector.collect_features(test_input)
            self.assertEqual(feature_vector.features, expected_feature_vectors)

    def test_features_calculator(self):
        grammar, _ = parse(
            os.path.join(self.dirname, "resources", "calculator.fan")
        )

        factory = FeatureFactory(grammar)
        features = factory.build()

        for f in features:
            print(f)

    def test_features_calculator_extended(self):
        grammar, _ = parse(
            os.path.join(self.dirname, "resources", "calculator_extended.fan")
        )

        factory = FeatureFactory(grammar)
        features = factory.build()

        for f in features:
            print(f)

    def test_features_from_grammar_star(self):
        grammar, _ = parse(
            os.path.join(self.dirname, "resources", "grammar_recursion_plus.fan")
        )

        inputs = ["1", "12", "3", "234234243789560243562", "a"]

        test_inputs = [FandangoInput.from_str(grammar, inp) for inp in inputs]
        import time

        start_time = time.time()
        collector = GrammarFeatureCollector(
            grammar,
        )
        for test_input in test_inputs:
            feature_vector = collector.collect_features(test_input)
            self.assertIsInstance(feature_vector, FeatureVector)

        print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    unittest.main()
