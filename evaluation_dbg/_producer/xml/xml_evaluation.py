import time
import xml.etree.ElementTree as ET

from fandango.evolution.algorithm import Fandango, LoggerLevel
from fandango.language.parse import parse

from fdlearn.data.oracle import OracleResult

def oracle(inp: str) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    try:
        ET.fromstring(str(inp))
    except ET.ParseError:
        return OracleResult.PASSING
    except Exception:
        return OracleResult.UNDEFINED
    return OracleResult.FAILING



def evaluate_xml(
    seconds=60,
):
    file = open("xml.fan", "r")
    grammar, constraints = parse(file, use_stdlib=False, use_cache=False)
    solutions = []

    time_in_an_hour = time.time() + seconds

    while time.time() < time_in_an_hour:
        fandango = Fandango(
            grammar,
            constraints,
            desired_solutions=100,
            logger_level=LoggerLevel.ERROR,
        )
        fandango.evolve()
        solutions.extend(fandango.solution)

    coverage = grammar.compute_grammar_coverage(solutions, 4)
    #coverage = grammar.compute_kpath_coverage(solutions, 4)

    valid = []
    for solution in solutions:
        if oracle(str(solution)):
            valid.append(solution)

    set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
    set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
    valid_percentage = len(valid) / len(solutions) * 100
    return (
        "XML",
        len(solutions),
        len(valid),
        valid_percentage,
        len(valid) / seconds,
        coverage,
        set_mean_length,
        set_medium_length,
    )


if __name__ == "__main__":
    print(evaluate_xml(seconds=60))