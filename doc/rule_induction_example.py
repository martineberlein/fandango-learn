from fandango.language.parse import parse
from fandango.language.symbol import NonTerminal

from fdlearn.resources.patterns import Pattern
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.data.input import FandangoInput
from fdlearn.learning.rule_induction.rule_induction import RuleInductionLearner
from fdlearn.interface.fandango import parse_contents
from fdlearn.learner import FandangoLearner

grammar = """
<start> ::= <arithexp>;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;
"""


if __name__ == "__main__":
    grammar, _ = parse_contents(grammar)

    valid_inputs = {
        FandangoInput.from_str(grammar, "sqrt(-12)", True),
        FandangoInput.from_str(grammar, "sqrt(-900)", True),
        FandangoInput.from_str(grammar, "sqrt(-2)", True),
        FandangoInput.from_str(grammar, "sqrt(-11234)", True),
        FandangoInput.from_str(grammar, "sqrt(12)", False),
        FandangoInput.from_str(grammar, "sqrt(0)", False),
        FandangoInput.from_str(grammar, "sqrt(0)", False),
        FandangoInput.from_str(grammar, "sqrt(2)", False),
        FandangoInput.from_str(grammar, "sin(3)", False),
        FandangoInput.from_str(grammar, "cos(4)", False),
        FandangoInput.from_str(grammar, "cos(-12)", False),
        FandangoInput.from_str(grammar, "cos(1012)", True),
        FandangoInput.from_str(grammar, "sqrt(101123)", True),
        FandangoInput.from_str(grammar, "sin(101231)", True),
        FandangoInput.from_str(grammar, "tan(1001)", True),

        }

    relevant_non_terminal = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    from time import time

    start_time = time()

    learner = RuleInductionLearner(
        grammar,
    )
    invariants = learner.learn_constraints(valid_inputs, relevant_non_terminals=relevant_non_terminal)

    print(time() - start_time)
    print(invariants)
    #
    # for inv in invariants:
    #     for rule in inv:
    #         print(rule)
    #     print("or")


