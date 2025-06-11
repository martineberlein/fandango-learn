import time
from debugging_benchmark.heartbleed.heartbleed import HeartbleedBenchmarkRepository

from fandango.evolution.algorithm import Fandango, LoggerLevel
from fandango.language.parse import parse


def evaluate_heartbleed(
    seconds=60,
) :
    file = open("Heartbleed.fan", "r")
    grammar, constraints = parse(file, use_stdlib=False, use_cache=False)
    solutions = []

    repo = HeartbleedBenchmarkRepository().build()[0]
    oracle = repo.get_oracle()

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
    #coverage = grammar.compute_kpath_coverage(solutions, 3)

    valid = []
    for solution in solutions:
        if oracle(str(solution)):
            valid.append(solution)

    set_mean_length = sum(len(str(x)) for x in valid) / len(valid)
    set_medium_length = sorted(len(str(x)) for x in valid)[len(valid) // 2]
    valid_percentage = len(valid) / len(solutions) * 100
    return (
        "Heartbleed",
        len(solutions),
        len(valid),
        valid_percentage,
        len(valid) / seconds,
        coverage,
        set_mean_length,
        set_medium_length,
    )


if __name__ == "__main__":
    print(evaluate_heartbleed(seconds=60))