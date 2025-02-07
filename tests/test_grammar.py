import unittest
import os

from fandangoLearner.interface.fandango import parse
from fandangoLearner.reduction.transformer import FuzzingBookGrammarTransformer


class TestConjunctionProcessor(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        self.grammar, self.constraints = parse(filename)


    def test_grammar_parsing(self):
        visitor = FuzzingBookGrammarTransformer()

        for non_term, node in self.grammar.rules.items():
            expansions = visitor.visit(node)
            visitor.grammar_[str(non_term)] = expansions


        for rule in visitor.grammar_:
            print(rule, visitor.grammar_[rule])
