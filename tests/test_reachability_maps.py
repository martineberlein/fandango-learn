import unittest
import os

from fandango.language.symbol import NonTerminal

from fdlearn.interface.fandango import parse
from fdlearn.reduction.feature_class import get_direct_reachable_non_terminals, get_direct_reachability_map

class FeatureExtraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dirname = os.path.dirname(__file__)
        cls.grammar, _ = parse(os.path.join(cls.dirname, "resources", "grammar.fan"))

    def test_direct_reachable_non_terminals(self):
        reachable_non_terminals = get_direct_reachable_non_terminals(self.grammar, NonTerminal("<string>"))

        self.assertIn(NonTerminal("<A>"), reachable_non_terminals)
        self.assertIn(NonTerminal("<B>"), reachable_non_terminals)
        self.assertEqual(len(reachable_non_terminals), 2)


    def test_get_direct_reachability_map(self):
        reachability_map = get_direct_reachability_map(self.grammar)

        print(reachability_map)
        self.assertIn(NonTerminal("<string>"), reachability_map[NonTerminal("<start>")])
        self.assertIn(NonTerminal("<A>"), reachability_map[NonTerminal("<string>")])
        self.assertIn(NonTerminal("<B>"), reachability_map[NonTerminal("<string>")])
        self.assertEqual(reachability_map[NonTerminal("<A>")], set())
        self.assertEqual(reachability_map[NonTerminal("<B>")], set())