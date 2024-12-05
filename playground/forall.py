from fandango.language.parse import parse, parse_file
from fandango.constraints.base import Constraint, ForallConstraint, NonTerminal, ComparisonConstraint
from fandango.language.search import RuleSearch, AttributeSearch
from fandango.evolution.algorithm import Fandango

def main_2():
    grammar, _ = parse_file("calculator.fan")

    inputs = list()
    for _ in range(2):
        inp = grammar.fuzz()
        inputs.append(inp)

    _, constraints = parse("(forall <container> in <digit>: int(<container>) == 5);")
    _, constraints = parse("(forall <container> in <number>: exists <elem> in <container>..<digit>: int(<elem>) == 1); len(str(<number>)) >= 4;")
    # _, constraints = parse("(forall <onenine> in <digit>: int(<onenine>) == 5) and (int(<number>) != 0);")
    # _, constraints = parse("int(<digit>) != 0 and len(str(<number>)) >= 3;")

    const = constraints[0]
    print(const.search)


    fandango = Fandango(grammar, constraints)
    solutions = fandango.evolve()
    for inp in solutions:
        print(inp)


    constraint = constraints[0]
    print(constraint)


if __name__ == "__main__":
    main_2()
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