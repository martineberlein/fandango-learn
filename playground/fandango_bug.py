from fandango.language.parse import parse_file


if __name__ == "__main__":
    grammar, constraints = parse_file("calculator.fan")

    # str(<maybeminus>) == '-';
    constraint = constraints[0]

    # sqrt(0) does not contain a '-', thus the constraint should evaluate to False.
    inp = grammar.parse("sqrt(0)")
    print("Check:", constraint.check(inp))
    assert constraint.check(inp) == False, f"{inp} does not contain a '-'."

