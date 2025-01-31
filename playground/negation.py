from fandango.constraints.base import ConjunctionConstraint

from fandangoLearner.language.constraints import NegationConstraint
from fandangoLearner.interface.fandango import parse_contents ,parse_constraint, parse_file
from fandangoLearner.data.input import FandangoInput
import random

GRAMMAR = """
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
    #grammar, _ = parse_contents(GRAMMAR, disable_logging=False)
    grammar, _ = parse_file("./calculator.fan", disable_logging=False)
    inp = "sqrt(-1)"
    inp = grammar.parse(inp)

    c = "int(<number>) >= 100;"
    constraint = parse_constraint(c, disable_logging=False)
    fitness = constraint.fitness(inp)
    print("Fitness, ", fitness.solved, fitness.total, fitness.success)

    negation = NegationConstraint(constraint)
    fitness = negation.fitness(inp)
    print("Fitness, ", fitness.solved, fitness.total, fitness.success)


    c = "str(<function>) == 'sqrt';"
    constraint = parse_constraint(c, disable_logging=False)
    from fandango.evolution.algorithm import Fandango, LoggerLevel

    test_constraint = ConjunctionConstraint([constraint, negation])
    print(test_constraint.check(inp))
    initial = []
    for _ in range(1000):
        initial.append(grammar.fuzz())

    fandango = Fandango(grammar, [test_constraint], logger_level=LoggerLevel.INFO, random_seed=1)
    results = fandango.evolve()

    solutions = set()
    for inp in results:
        solutions.add(FandangoInput(inp))

    print(solutions)


