from fandango.evolution.algorithm import Fandango
from fandango.language.parse import parse_file

if __name__ == '__main__':
    # Parse grammar and constraints
    grammar, constraints = parse_file('calculator.fan')

    for _ in range(1):
        # Initialize FANDANGO
        fandango = Fandango(grammar, constraints, verbose=True)

        # Evolve solutions
        solutions = fandango.evolve()

        # Print solutions
        for solution in solutions:
            print(str(solution))