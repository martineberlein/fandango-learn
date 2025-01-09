import logging
from typing import Dict, Tuple

from debugging_framework.input.oracle import OracleResult
from fandango.language.symbol import NonTerminal
from fandango.evolution.algorithm import Fandango

from evaluation.heartbleed.heartbeat import oracle
from fandangoLearner.data.input import FandangoInput
from fandangoLearner.interface.fandango import parse
from fandangoLearner.learner import FandangoLearner


def dfs(tree, action):
    node, children = tree.symbol, tree.children
    action(tree)
    for child in children:
        dfs(child, action)

def get_subtree(tree, path: Tuple[int, ...]):
    """Access a subtree based on `path` (a list of children numbers)"""

    curr_node = tree
    while path:
        #print(curr_node[0])
        curr_node = curr_node[path[0]]
        path = path[1:]

    return curr_node

def tree_to_string(tree):
    node, children = tree.symbol, tree.children
    if not children:
        return node
    return ''.join(str(tree_to_string(child)) for child in children)


LANG_GRAMMAR = """
<start> ::= <stmt>;
<stmt> ::= <assgn> | <assgn> "; " <stmt>;
<assgn> ::= <var> ":=" <rhs>;
<rhs> ::= <var> | <digit>;
<var> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z";
<digit>::=  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
"""

def eval_lang(inp_tree):
    def assgnlhs(assgn):
        return tree_to_string(get_subtree(assgn, (0,)))

    def assgnrhs(assgn):
        return tree_to_string(get_subtree(assgn, (2,)))

    valueMap = {}

    def evalAssignments(tree):
        node, children = tree.symbol, tree.children
        if node == NonTerminal("<assgn>"):
            lhs = assgnlhs(tree)
            rhs = assgnrhs(tree)
            if rhs.isdigit():
                valueMap[lhs] = int(rhs)
            else:
                valueMap[lhs] = valueMap[rhs]

    dfs(inp_tree, evalAssignments)

    return valueMap

def validate_lang(inp: FandangoInput):
    try:
        eval_lang(inp.tree)
        return OracleResult.FAILING
    except Exception as e:
        return OracleResult.PASSING


CONSTRAINTS = """
forall <use> in <assgn>.<rhs>:
    exists <def> in <assgn>:
        str(<def>.<var>) == str(<use>.<var>) and is_before(<start>, <def>, <use>)
;

forall <assgn> in <assgn>:
    str(<assgn>.<var>) != str(<assgn>.<rhs>.<var>)
;
"""

def generate_valid():
    grammar, constraints = parse(LANG_GRAMMAR + CONSTRAINTS)
    print(constraints[0].check(grammar.parse("a:=1; b:=a; c:=2")))
    fandango = Fandango(
        grammar, constraints, desired_solutions=200
    )
    solutions = fandango.evolve()
    for solution in solutions:
        print(solution)


if __name__ == "__main__":

    generate_valid()
    exit()

    grammar, _ = parse(LANG_GRAMMAR)

    valid_inp = FandangoInput.from_str(grammar, "a:=1; b:=a; c:=2")
    invalid_inp = FandangoInput.from_str(grammar, "a:=1; b:=a; c:=x")
    inps = FandangoInput.from_str(grammar, "e:=1")
    assert validate_lang(valid_inp) == OracleResult.FAILING
    assert validate_lang(invalid_inp) == OracleResult.PASSING
    assert validate_lang(inps) == OracleResult.FAILING

    test_inputs = set()
    for _ in range(100):
        inp = grammar.fuzz()
        inp = FandangoInput(inp)
        inp.oracle = validate_lang(inp)
        test_inputs.add(inp)

    for inp in test_inputs:
        print(inp, inp.oracle)

    learner = FandangoLearner(
        grammar
    )
    learned_constraints = learner.learn_constraints(test_inputs)

    for constraint in learner.get_best_candidates():
        print(constraint)
