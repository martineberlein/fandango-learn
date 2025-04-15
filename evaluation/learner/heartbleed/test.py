import os

from fandango.evolution.algorithm import Fandango

from fdlearn.interface.fandango import parse_file, parse_constraint

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "heartbleed.fan")
    grammar, _ = parse_file(filename)

    constraint = "where len(<payload>) == int(<payloadlength>)"
    constraint = parse_constraint(constraint)

    constraint2 = "where int(<payloadlength>) == 5"
    constraint2 = parse_constraint(constraint2)

    fandango = Fandango(grammar=grammar, constraints=[constraint, constraint2])

    for _ in range(2):
        solutions = fandango.evolve()
        for inp in solutions:
            print(inp)