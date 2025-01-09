from typing import Dict, Tuple

from islearn.learner import InvariantLearner
from isla.language import ISLaUnparser, Formula
from islearn.parse_tree_utils import dfs, get_subtree, tree_to_string

from isla.language import DerivationTree
from isla.parser import EarleyParser
from isla.type_defs import ParseTree
import string

LANG_GRAMMAR = {
    "<start>":
        ["<stmt>"],
    "<stmt>":
        ["<assgn>", "<assgn> ; <stmt>"],
    "<assgn>":
        ["<var> := <rhs>"],
    "<rhs>":
        ["<var>", "<digit>"],
    "<var>": list(string.ascii_lowercase),
    "<digit>": list(string.digits)
}


def eval_lang(inp: str) -> Dict[str, int]:
    def assgnlhs(assgn: ParseTree):
        return tree_to_string(get_subtree(assgn, (0,)))

    def assgnrhs(assgn: ParseTree):
        return tree_to_string(get_subtree(assgn, (2,)))

    valueMap: Dict[str, int] = {}
    tree = list(EarleyParser(LANG_GRAMMAR).parse(inp))[0]

    def evalAssignments(tree):
        node, children = tree
        if node == "<assgn>":
            lhs = assgnlhs(tree)
            rhs = assgnrhs(tree)
            if rhs.isdigit():
                valueMap[lhs] = int(rhs)
            else:
                valueMap[lhs] = valueMap[rhs]

    dfs(tree, evalAssignments)

    return valueMap

def validate_lang(inp: DerivationTree) -> bool:
    try:
        eval_lang(str(inp))
        return True
    except Exception:
        return False

if __name__ == "__main__":

    result: Dict[Formula, Tuple[float, float]] = InvariantLearner(
        LANG_GRAMMAR,
        prop=validate_lang,
        # activated_patterns={
        #     "Def-Use (reST Strict)",  # Optional; leads to quicker results
        # },
    ).learn_invariants()

    print("\n".join(map(
        lambda p: f"{p[1]}: " + ISLaUnparser(p[0]).unparse(),
        {f: p for f, p in result.items() if p[0] > .0}.items())))