import math

from debugging_framework.input.oracle import OracleResult
from fandango.language.symbol import NonTerminal

from fandangoLearner.interface.fandango import parse
from fandangoLearner.learner import FandangoLearner, FandangoInput
from fandangoLearner.refinement.generator import Generator
from fandangoLearner.refinement.core import FandangoRefinement


def calculator_oracle(inp):
    try:
        eval(
            str(inp), {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan}
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


GRAMMAR = """
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
        tree = self.grammar.fuzz()

        return FandangoInput(tree)


def check_generator(grammar):
    generator = FandangoGenerator(grammar)
    for _ in range(10):
        print(generator.generate())


if __name__ == "__main__":
    parsed_grammar, _ = parse(GRAMMAR)

    relevant_non_terminals = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    fandangoRE = FandangoRefinement(
        grammar=parsed_grammar,
        oracle=calculator_oracle,
        initial_inputs=["cos(12)", "sqrt(-900)"],
        relevant_non_terminals=relevant_non_terminals,
    )

    const = fandangoRE.explain()
    print(fandangoRE.learner.get_candidates())
    for candidate in const:
        print(candidate)
