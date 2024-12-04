from fandango.language.parse import parse
from fandango.constraints.base import Constraint, ForallConstraint

if __name__ == "__main__":
    _, constraint = parse("forall <tree> in <NON_TERMINAL>: <tree>/<xml_open_tag>/<id> == <tree>/<xml_close_tag>/<id>;")

    constraint = constraint[0]
    print(constraint)
    print(constraint.bound)
    print(constraint.statement.searches)
    for search in constraint.statement.searches.values():
        print(type(search))
    print(constraint.search)
    print(constraint.searches)