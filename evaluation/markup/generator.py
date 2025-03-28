import os

from debugging_benchmark.markup.markup import MarkupBenchmarkRepository

from fandango.evolution.algorithm import Fandango

from fdlearn.interface.fandango import parse

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "markup_gen.fan")
    grammar, constraints = parse(filename)

    programs = MarkupBenchmarkRepository().build()
    program = programs[0]  # Markup.1
    oracle = program.oracle

    fandango = Fandango(grammar, constraints)

    solutions = fandango.evolve()

    for sol in solutions:
        print(sol, program.oracle(str(sol)))

    for inp in program.get_initial_inputs():
        print(inp, oracle(inp))