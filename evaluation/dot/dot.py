import logging
import os
import re
import urllib.request
from pathlib import Path

import dill as pickle
import isla.fuzzer
from grammar_graph import gg
from isla import language
from isla.evaluator import evaluate
from isla.language import ISLaUnparser, DerivationTree
from isla.parser import PEGParser

from islearn.learner import InvariantLearner

from islearn_example_languages import render_dot, DOT_GRAMMAR


def setup_directories(base_dir):
    input_dir = Path(base_dir) / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    return input_dir


def download_and_clean_dot_file(url):
    with urllib.request.urlopen(url) as f:
        dot_code = f.read().decode("utf-8").strip()
        dot_code = re.sub(r"(^|\n)\s*//.*?(\n|$)", "", dot_code)
        dot_code = dot_code.replace("\\n", "\n").replace("\r\n", "\n")
        dot_code = re.compile(r"/\*.*?\*/", re.DOTALL).sub("", dot_code)

    if not render_dot(dot_code):
        raise ValueError(f"Invalid DOT code from URL: {url}")
    return dot_code


def parse_and_reduce(parser, reducer, dot_code):
    try:
        sample_tree = language.DerivationTree.from_parse_tree(
            list(parser.parse(dot_code))[0]
        )
        reduced_tree = reducer.reduce_by_smallest_subtree_replacement(sample_tree)
    except SyntaxError as e:
        raise ValueError(f"Failed to parse or reduce DOT code: {e}")

    return sample_tree, reduced_tree


