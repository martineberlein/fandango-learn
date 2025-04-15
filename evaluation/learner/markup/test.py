import os

from fdlearn.interface import parse_constraint
from fdlearn.interface.fandango import parse_file, parse_constraint


if __name__ == '__main__':
    from fdlearn.resources.patterns import Pattern

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "markup_gen.fan")
    grammar, _ = parse_file(filename)

    constraint = parse_constraint("""exists <elem> in <text>: str_contains(<elem>, '"');""")

    print(constraint)
    inp = grammar.parse('auhun"hbzb')
    print(inp.to_tree())
    print(constraint.check(inp))

