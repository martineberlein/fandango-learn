from fandango.language.parse import parse, parse_file
from fandango.constraints.base import Constraint, ForallConstraint, NonTerminal, ComparisonConstraint, Comparison
from fandango.language.search import RuleSearch, AttributeSearch
from fandango.evolution.algorithm import Fandango
from fandango.constraints import predicates


def main_2():
    grammar, _ = parse_file("calculator.fan")

    inputs = list()
    for _ in range(2):
        inp = grammar.fuzz()
        inputs.append(inp)

    _, constraints = parse("(forall <container> in <digit>: int(<container>) == 5);")
    # _, constraints = parse("(forall <container> in <number>: exists <elem> in <container>..<digit>: int(<elem>) == 1); len(str(<number>)) >= 4;")
    # _, constraints = parse("(forall <onenine> in <digit>: int(<onenine>) == 5) and (int(<number>) != 0);")
    # _, constraints = parse("int(<digit>) != 0 and len(str(<number>)) >= 3;")

    const: ForallConstraint = constraints[0]
    print(const.search)
    print(type(const.search))
    print("Search Symbold: ", const.search.symbol)
    print("Bound: ", const.bound)
    print("Type Bound: ", type(const.bound))
    print(const.statement)
    print("Statement Searches: ", const.statement.searches)
    print("Statement Searches Values: ", const.statement.searches)

    for name, search in const.statement.searches.items():
        print(name, search)
        print("Search Type: ", type(search))

    const_1 = ForallConstraint(
        statement=ComparisonConstraint(
            operator=Comparison.EQUAL,
            left="int(___fandango_4405260464_6___)",
            right="5",
            searches={"___fandango_4405260464_6___": RuleSearch(NonTerminal("<container>"))},
            local_variables=predicates.__dict__,
            global_variables=globals(),
        ),  # Needs to change
        bound=NonTerminal("<container>"),
        search=RuleSearch(symbol=NonTerminal("<number>")),
        local_variables=predicates.__dict__,
        global_variables=globals(),
    )

    print(const_1)

    fandango = Fandango(grammar, [const_1])
    solutions = fandango.evolve()
    for inp in solutions:
        print(inp)

    constraint = constraints[0]
    print(constraint)

    assert const == const_1

def main_3():
    import time

    parser_start = time.time()
    grammar, constraints = parse_file("calculator.fan")
    parser_end = time.time()

    print(f"Time taken to parse grammar and constraints: {parser_end - parser_start:.2f} seconds")

    fuzzing_start = time.time()
    fandango = Fandango(grammar, constraints)
    solutions = fandango.evolve()

    fuzzing_end = time.time()
    print(f"Time taken to fuzz and find solutions: {fuzzing_end - fuzzing_start:.2f} seconds")

    for inp in solutions:
        print(inp)


if __name__ == "__main__":
    main_3()
    exit(0)

    _, constraint = parse("forall <tree> in <NON_TERMINAL>: <tree>/<xml_open_tag>/<id> == <tree>/<xml_close_tag>/<id>;")

    constraint: ForallConstraint = constraint[0]
    print(constraint)
    print(constraint.bound)
    print(constraint.statement.searches)
    for search in constraint.statement.searches.values():
        print(type(search), type(search.base), type(search.base.base), search.base.base.symbol, search.attribute)
    print(constraint.search)
    print(constraint.searches)

    const = ForallConstraint(
        statement=ComparisonConstraint(
            left="None",
            right="None",
            operator="==",
            searches={}, # Needs to change Attribute Searches
        ), # Needs to change
        bound=NonTerminal("<var>"),
        search=RuleSearch(symbol=NonTerminal("<NON_TERMINAL>")) # Needs to change
    )