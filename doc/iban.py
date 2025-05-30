from fandango.evolution.algorithm import Fandango

from fdlearn.data import OracleResult
from fdlearn.learner import FandangoLearner, FandangoInput
from fdlearn.interface.fandango import parse_contents
from fdlearn.logger import LoggerLevel
from fdlearn.resources.patterns import Pattern

grammar = """
<start> ::= <iban>;
<iban> ::= <county><checksum><bban>;
<county> ::= "DE" | "AT" | "CH" | "ES" | "FR" | "IT" | "NL" | "BE" | "LU" | "GB";
<checksum> ::= <digit><digit>;
<bban> ::= <digit>+;
<digit>::=  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
"""

def validate_iban(iban: str) -> bool:
    """
    Very simple IBAN validity check:
      - No per-country length verification.
    """
    rotated = iban[4:] + iban[:4]
    num_str = ''.join(str(int(ch, 36)) for ch in rotated)
    try:
        return int(num_str) % 97 == 1
    except ValueError:
        return False


def oracle(iban: str) -> OracleResult:
    """
    Oracle function to validate IBANs.
    """
    return OracleResult.PASSING if validate_iban(str(iban)) else OracleResult.FAILING


if __name__ == "__main__":
    grammar, _ = parse_contents(grammar)

    positive, negative = set(), set()
    while True:
        tree = grammar.fuzz()
        inp = tree.to_string()
        if validate_iban(inp):
            positive.add(inp)
            break
        else:
            negative.add(inp)

    print(f"Found {len(positive)} vaild and {len(negative)} invalid IBANs.")

    positive_inputs = {FandangoInput.from_str(grammar, inp, True) for inp in positive}
    negative_inputs = {FandangoInput.from_str(grammar, inp, False) for inp in negative}
    initial_inputs = positive_inputs.union(negative_inputs)

    pattern = [
        Pattern(
            string_pattern="""
def iban_checksum(country: str, bban: str) -> str:
    moved = bban + country + "00"
    numeric = "".join(str(int(ch, 36)) for ch in moved)
    remainder = int(numeric) % 97
    return 98 - remainder

where iban_checksum(str(<NON_TERMINAL>),str(<NON_TERMINAL>)) == int(<NON_TERMINAL>)
"""
        )
    ]

    learner = FandangoLearner(grammar, patterns=pattern)
    learned_constraints = learner.learn_constraints(
        initial_inputs,
    )

    invariant = learner.get_best_candidates()[0].constraint

    print("Using Invariant ", invariant, " to generate valid IBANs", end="\n\n")

    solutions = set()

    while len(solutions) < 100:
        fandango = Fandango(grammar, [invariant], desired_solutions=100)
        population = fandango.evolve()
        for tree in population:
            solutions.add(tree)

    tp = [True for tree in solutions if validate_iban(str(tree))]
    fp = [True for tree in solutions if not validate_iban(str(tree))]

    print("--- Invariant Evaluation ---")
    print(f"Generated {len(tp)} valid IBANs and {len(fp)} invalid IBANs.")
