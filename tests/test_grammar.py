import unittest
from pathlib import Path
import os

from fandango.constraints.base import DisjunctionConstraint
from fandango.language.symbol import NonTerminal

from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse_file, parse_constraint, parse
from fandangoLearner.learning.candidate import FandangoConstraintCandidate
from fandangoLearner.learning.combination import ConjunctionProcessor, DisjunctionProcessor
from fandangoLearner.learning.candidate import CandidateSet
from fandangoLearner.reduction.transformer import NameGrammarVisitor


class TestConjunctionProcessor(unittest.TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "resources", "calculator.fan")
        self.grammar, self.constraints = parse(filename)


    def test_grammar_parsing(self):

        start_node = self.grammar.rules[NonTerminal("<arithexp>")]

        visitor = NameGrammarVisitor()
        #  print(visitor.visit(start_node))

        for non_term, node in self.grammar.rules.items():
            expansions = visitor.visit(node)
            visitor.grammar_[str(non_term)] = expansions


        for rule in visitor.grammar_:
            print(rule, visitor.grammar_[rule])
