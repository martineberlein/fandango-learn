import math
from pathlib import Path

from fandango.language.parse import parse
from fdlearn.data.oracle import OracleResult

from examples.subjects.subject import Subject


def calculator_oracle(inp):
    try:
        eval(
            str(inp),
            {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan},
        )
    except ValueError:
        return OracleResult.FAILING
    return OracleResult.PASSING


def get_calculator_subject() -> Subject:
    base_dir = Path(__file__).parent
    with open(base_dir / "calculator.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = set()

    return Subject(
        name="Calculator",
        grammar=grammar,
        initial_inputs=initial_inputs,
        oracle=calculator_oracle
    )