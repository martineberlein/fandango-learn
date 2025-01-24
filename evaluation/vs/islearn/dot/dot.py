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

from islearn.helpers import tree_in
from islearn.learner import InvariantLearner
from islearn.mutation import MutationFuzzer
from islearn.reducer import InputReducer
from islearn_example_languages import render_dot, DOT_GRAMMAR

logging.basicConfig(level=logging.DEBUG)


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


def load_or_generate_trees(urls, input_dir, parser, reducer):
    positive_trees = []
    reduced_trees = []

    for url in urls:
        file_name = url.split("/")[-1]
        tree_file = input_dir / f"{file_name}.tree"
        reduced_tree_file = input_dir / f"{file_name}.reduced.tree"

        if tree_file.exists() and reduced_tree_file.exists():
            with open(tree_file, "rb") as file:
                positive_trees.append(pickle.loads(file.read()))

            with open(reduced_tree_file, "rb") as file:
                reduced_trees.append(pickle.loads(file.read()))
            continue

        dot_code = download_and_clean_dot_file(url)
        sample_tree, reduced_tree = parse_and_reduce(parser, reducer, dot_code)

        with open(tree_file, "wb") as sample_file:
            sample_file.write(pickle.dumps(sample_tree))
        with open(reduced_tree_file, "wb") as reduced_file:
            reduced_file.write(pickle.dumps(reduced_tree))

        positive_trees.append(sample_tree)
        reduced_trees.append(reduced_tree)

    return positive_trees, reduced_trees


def learn_invariants(grammar, positive_examples, prop):
    learner = InvariantLearner(
        grammar,
        prop=prop,
        activated_patterns={"String Existence"},
        positive_examples=positive_examples,
        target_number_positive_samples=50,
        target_number_negative_samples=50,
        max_disjunction_size=2,
        filter_inputs_for_learning_by_kpaths=False,
        min_recall=1,
        min_specificity=0.8,
        reduce_inputs_for_learning=False,
        generate_new_learning_samples=False,
        exclude_nonterminals={
            "<WS>",
            "<WSS>",
            "<MWSS>",
            "<esc_or_no_string_endings>",
            "<esc_or_no_string_ending>",
            "<no_string_ending>",
            "<LETTER_OR_DIGITS>",
            "<LETTER>",
            "<maybe_minus>",
            "<maybe_comma>",
            "<maybe_semi>",
        },
    )
    return learner.learn_invariants()


def evaluate_invariants(
    best_invariant, validation_inputs, negative_validation_inputs, grammar, graph
):
    tp, tn, fp, fn = 0, 0, 0, 0

    for inp in validation_inputs:
        if evaluate(best_invariant, inp, grammar, graph=graph).is_true():
            tp += 1
        else:
            fn += 1

    for inp in negative_validation_inputs:
        if evaluate(best_invariant, inp, grammar, graph=graph).is_true():
            fp += 1
        else:
            tn += 1

    return tp, tn, fp, fn


def main():
    dirname = os.path.abspath(os.path.dirname(__file__))
    input_dir = setup_directories(dirname)

    parser = PEGParser(DOT_GRAMMAR)
    reducer = InputReducer(DOT_GRAMMAR, render_dot, k=3)
    graph = gg.GrammarGraph.from_grammar(DOT_GRAMMAR)

    urls = [
        "https://raw.githubusercontent.com/ecliptik/qmk_firmware-germ/56ea98a6e5451e102d943a539a6920eb9cba1919/users/dennytom/chording_engine/state_machine.dot",
        "https://raw.githubusercontent.com/Ranjith32/linux-socfpga/30f69d2abfa285ad9138d24d55b82bf4838f56c7/Documentation/blockdev/drbd/disk-states-8.dot",
        "https://raw.githubusercontent.com/gmj93/hostap/d0deb2a2edf11acd6eb6440336406228eeeab96e/doc/p2p_sm.dot",
        "https://raw.githubusercontent.com/nathanaelle/wireguard-topology/f0e42d240624ca0aa801d890c1a4d03d5901dbab/examples/3-networks/topology.dot",
        "https://raw.githubusercontent.com/210296kaczmarek/student-forum-poprawione/55790569976d4e92a32d9471d3549943011fcb70/vendor/bundle/ruby/2.4.0/gems/ruby-graphviz-1.2.3/examples/dot/genetic.dot",
        "https://raw.githubusercontent.com/Cloudofyou/tt-demo/5504ac17790d3863bf036f6ce8d651a862fa6b0f/tt-demo.dot",
    ]

    positive_trees, reduced_trees = load_or_generate_trees(
        urls, input_dir, parser, reducer
    )
    learning_inputs = reduced_trees[:3]
    validation_inputs = positive_trees[3:]

    invariants = learn_invariants(DOT_GRAMMAR, learning_inputs, render_dot)
    best_invariant, (specificity, sensitivity) = next(iter(invariants.items()))

    print(
        f"Best invariant (*estimated* specificity {specificity:.2f}, sensitivity: {sensitivity:.2f}):"
    )
    print(ISLaUnparser(best_invariant).unparse())

    tp, tn, fp, fn = evaluate_invariants(
        best_invariant, validation_inputs, [], DOT_GRAMMAR, graph
    )
    print(f"TP: {tp} | FN: {fn} | FP: {fp} | TN: {tn}")


if __name__ == "__main__":
    main()
