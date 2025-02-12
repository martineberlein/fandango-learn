import math

from debugging_framework.input.oracle import OracleResult

from fdlearn.interface.fandango import parse
from fdlearn.learner import FandangoLearner, FandangoInput
from fdlearn.refinement.generator import Generator
from fdlearn.refinement.core import HypothesisInputFeatureDebugger


def calculator_oracle(inp):
    try:
        eval(
            str(inp),
            {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan},
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
