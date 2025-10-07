from pathlib import Path
from fdlearn.data import OracleResult
from fandango.language.parse import parse

from examples.subjects.subject import Subject


def middle(x, y, z):
    m = z
    if y < z:
        if x < y:
            m = y
        elif x < z:
            m = y
    else:
        if x > y:
            m = y
        elif x > z:
            m = x
    return m


def middle_oracle(x, y, z):
    sorted_list = sorted([x, y, z])
    return sorted_list[1]


def oracle(inp):
    x, y, z = map(lambda x: int(x), str(inp).split(" "))
    return OracleResult.PASSING if middle(x, y, z) == middle_oracle(x, y, z) else OracleResult.FAILING


def get_middle_subject() -> Subject:
    base_dir = Path(__file__).parent
    with open(base_dir / "middle.fan", "r") as file:
        grammar, _ = parse(file, use_cache=False, use_stdlib=False)

    initial_inputs = set()

    return Subject(
        name="Middle",
        grammar=grammar,
        initial_inputs=initial_inputs,
        oracle=oracle
    )