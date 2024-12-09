import time

from fandango.language.parse import parse_file, parse
from fandango.language.symbol import NonTerminal

from fandangoLearner.learner import FandangoLearner
from fandangoLearner.data.input import FandangoInput, OracleResult
from fandangoLearner.learning.instantiation import NonTerminalPlaceholderTransformer, ValuePlaceholderTransformer
from fandangoLearner.learning.candidate import FandangoConstraintCandidate

from calculator import calculator_oracle


if __name__ == "__main__":
    grammar, _ = parse_file("calculator.fan")
    test_inputs = [
        ("sqrt(-900)", OracleResult.FAILING),
        ("sqrt(-1)", OracleResult.FAILING),
        ("sin(-900)", OracleResult.PASSING),
        ("sqrt(2)", OracleResult.PASSING),
        ("cos(10)", OracleResult.PASSING),
    ]

    initial_inputs = {
        FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs
    }
    for _ in range(100):
        inp = grammar.fuzz()
        test_inputs.append((str(inp), calculator_oracle(inp)))

    non_terminal_values = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    start_time = time.time()
    learner = FandangoLearner(grammar)
    end_time = time.time()
    print(f"Time taken to initialize learner: {end_time - start_time:.4f} seconds")

    patterns = learner.patterns

    start_time = time.time()
    inst_pattern = []
    for pattern in patterns:
        transformer = NonTerminalPlaceholderTransformer(non_terminal_values)
        #print("Pattern: ", pattern)
        pattern.accept(transformer)
        transformed = transformer.results
        inst_pattern.extend(transformed)

        for num, trans in enumerate(transformed):
            # print(f"{num} Constraint: ", trans)
            pass

    for f in inst_pattern:
        print(f)

    value_map = learner.extract_non_terminal_values(
        relevant_non_terminals=non_terminal_values,
        initial_inputs={inp for inp in initial_inputs if inp.oracle == OracleResult.FAILING},
    )

    final = []
    for pattern in inst_pattern:
        transformer = ValuePlaceholderTransformer(value_map)
        pattern.accept(transformer)
        transformed = transformer.results
        final.extend(transformed)

    cands = []
    for pattern in final:
        candidate = FandangoConstraintCandidate(pattern)
        try:
            candidate.evaluate(initial_inputs)
            cands.append(candidate)
        except Exception:
            continue

    end_time = time.time()
    print(f"Time taken to instantiate patterns: {end_time - start_time:.4f} seconds")
    print("Instantiated Patterns: ", len(cands))

    for cand in cands:
        print("Constraint: ", cand.constraint)
        print("Recall: ", cand.recall())
        print("Precision: ", cand.precision())
        print("\n")