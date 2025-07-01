import unittest
import os

from fandango.language.symbol import NonTerminal
from fandango.language.parse import parse

from fdlearn.learning.value_map import get_reachability_map_level
from fdlearn.reduction.feature_class import (
    get_direct_reachable_non_terminals,
    get_direct_reachability_map,
)
from .utils import RESOURCES_ROOT


class FeatureExtraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(RESOURCES_ROOT / "grammar.fan", "r") as grammar_file:
            cls.grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

    def test_direct_reachable_non_terminals(self):
        reachable_non_terminals = get_direct_reachable_non_terminals(
            self.grammar, NonTerminal("<string>")
        )

        self.assertIn(NonTerminal("<A>"), reachable_non_terminals)
        self.assertIn(NonTerminal("<B>"), reachable_non_terminals)
        self.assertEqual(len(reachable_non_terminals), 2)

    def test_get_direct_reachability_map(self):
        reachability_map = get_direct_reachability_map(self.grammar)

        self.assertIn(NonTerminal("<string>"), reachability_map[NonTerminal("<start>")])
        self.assertIn(NonTerminal("<A>"), reachability_map[NonTerminal("<string>")])
        self.assertIn(NonTerminal("<B>"), reachability_map[NonTerminal("<string>")])
        self.assertEqual(reachability_map[NonTerminal("<A>")], set())
        self.assertEqual(reachability_map[NonTerminal("<B>")], set())

    def test_get_direct_reachability_map_level(self):
        reachability_map = get_reachability_map_level(self.grammar)
        expected_map = {
            NonTerminal("<start>"): {
                0: {NonTerminal("<string>")},
                1: {NonTerminal("<A>"), NonTerminal("<B>")},
            },
            NonTerminal("<string>"): {
                0: {NonTerminal("<A>"), NonTerminal("<B>")},
            },
            NonTerminal("<A>"): {},
            NonTerminal("<B>"): {},
        }

        self.assertEqual(reachability_map, expected_map)

    def test_get_reachability_map_level(self):
        with open(RESOURCES_ROOT / "grammar_recursion.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        reachability_map = get_reachability_map_level(grammar)
        expected_map = {
            NonTerminal("<start>"): {
                0: {NonTerminal("<string>")},
                1: {NonTerminal("<B>"), NonTerminal("<A>")},
                2: {NonTerminal("<digit>"), NonTerminal("<char>")},
            },
            NonTerminal("<string>"): {
                0: {NonTerminal("<B>"), NonTerminal("<A>")},
                1: {NonTerminal("<digit>"), NonTerminal("<char>")},
            },
            NonTerminal("<A>"): {0: {NonTerminal("<A>"), NonTerminal("<char>")}},
            NonTerminal("<char>"): {},
            NonTerminal("<B>"): {0: {NonTerminal("<B>"), NonTerminal("<digit>")}},
            NonTerminal("<digit>"): {},
        }

        self.assertEqual(reachability_map, expected_map)

    def test_get_reachability_map_more_paths(self):
        with open(RESOURCES_ROOT / "reachable.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        reachability_map = get_reachability_map_level(grammar)
        expected_map = {
            NonTerminal("<start>"): {
                0: {NonTerminal("<string>")},
                1: {NonTerminal("<A>"), NonTerminal("<B>")},
                # 2: {NonTerminal("<B>")},
            },
            NonTerminal("<string>"): {
                0: {NonTerminal("<A>"), NonTerminal("<B>")},
                # 1: {NonTerminal("<B>")},
            },
            NonTerminal("<A>"): {0: {NonTerminal("<B>")}},
            NonTerminal("<B>"): {},
        }
        self.assertEqual(reachability_map, expected_map)

    def test_get_reachability_map_xml(self):
        with open(RESOURCES_ROOT / "xml.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        reachability_map = get_reachability_map_level(grammar)


    def test_grammar_dijkstra(self):
        from fdlearn.learning.value_map import ReachabilityMap
        with open(RESOURCES_ROOT / "xml.fan", "r") as grammar_file:
            grammar, _ = parse(grammar_file, use_cache=False, use_stdlib=False)

        reachability_map = ReachabilityMap(grammar)
        path = reachability_map.shortest_path(NonTerminal("<start>"), NonTerminal("<id>"))
        print(path)
        path = reachability_map.shortest_path(NonTerminal("<start>"), NonTerminal("<text_char>"))
        print(path)

        paths = reachability_map.get_all_shortest_paths(NonTerminal("<start>"), NonTerminal("<id>"))
        print("All shortest paths from <start> to <id>:")
        for path in paths:
            print(path)

if __name__ == "__main__":
    unittest.main()
