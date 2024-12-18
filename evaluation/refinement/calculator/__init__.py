from avicenna.core import HypothesisInputFeatureDebugger, CandidateLearner, Generator
from avicenna.data import Input

from fandangoLearner.core import ConstraintCandidateLearner
from fandangoLearner.learner import FandangoLearner, FandangoInput
from fandangoLearner.interface.fandango import parse
import math
from debugging_framework.input.oracle import OracleResult

def calculator_oracle(inp):
    try:
        eval(
            str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
        )
    except ValueError:
        return OracleResult.FAILING, ValueError()
    return OracleResult.PASSING, None



grammar = """
<start> ::= <arithexp>;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= "" |<digit><maybedigits>;
<digit>::=  "0" | <onenine>;
"""


class FandangoGenerator(Generator):

    def __init__(self, grammar, **kwargs):
        super().__init__(grammar, **kwargs)

    def generate(self, *args, **kwargs) -> FandangoInput:
        tree = grammar.fuzz()

        return FandangoInput(tree)


if __name__ == "__main__":
    grammar, _ = parse(grammar)

    avicenna = HypothesisInputFeatureDebugger(
        grammar=grammar,
        oracle=calculator_oracle,
        initial_inputs=["cos(12)", "sqrt(-900)"],
        learner=FandangoLearner(grammar),
        generator=FandangoGenerator(grammar),
    )

    const = avicenna.explain()
