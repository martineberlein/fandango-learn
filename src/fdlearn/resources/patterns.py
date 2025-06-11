from typing import Optional

from fandango.constraints.base import ComparisonConstraint, Constraint, Comparison
from fandango.constraints import predicates
from fandango.language.search import RuleSearch
from fandango.language.symbol import NonTerminal

from fdlearn.interface.fandango import parse_file, parse_constraint
from fdlearn.data import FandangoInput


class Pattern:
    """
    A class to represent a pattern in the Fandango language.
    New patterns can be added by creating a new instance of this class.
    They will be automatically added to the registry.
    By providing the instantiated patterns, the setup of the learner is significantly faster, since the patterns
    are already instantiated. Parsing the patterns is expensive and a time-consuming process.
    """

    registry = []

    def __init__(
        self,
        string_pattern: str,
        instantiated_pattern: Optional[Constraint] = None,
        use_cache: bool = True,
    ):
        self.string_pattern = string_pattern
        self.instantiated_pattern = instantiated_pattern or parse_constraint(
            string_pattern
        )
        self.__class__.registry.append(self)

    @classmethod
    def get_id(cls, i):
        return f"___fandango_01_{i}___"

    def __repr__(self):
        return f"Pattern({self.string_pattern})"


Pattern(
    string_pattern="str(<NON_TERMINAL>) == <STRING>;",
    instantiated_pattern=ComparisonConstraint(
        operator=Comparison.EQUAL,
        left=f"str({Pattern.get_id(1)})",
        right=f"{Pattern.get_id(2)}",
        searches={
            Pattern.get_id(1): RuleSearch(NonTerminal("<NON_TERMINAL>")),
            Pattern.get_id(2): RuleSearch(NonTerminal("<STRING>")),
        },
        local_variables=predicates.__dict__,
        global_variables=globals(),
    ),
)

for operator in Comparison:
    Pattern(
        string_pattern=f"int(<NON_TERMINAL>) {operator} len(str(<NON_TERMINAL>));",
        instantiated_pattern=ComparisonConstraint(
            operator=operator,
            left=f"int({Pattern.get_id(1)})",
            right=f"len(str({Pattern.get_id(2)}))",
            searches={
                Pattern.get_id(1): RuleSearch(NonTerminal("<NON_TERMINAL>")),
                Pattern.get_id(2): RuleSearch(NonTerminal("<NON_TERMINAL>")),
            },
            local_variables=predicates.__dict__,
            global_variables=globals(),
        ),
    )

# All Patterns with the form int(<NON_TERMINAL>) <operator> <INTEGER>;
for operator in Comparison:
    Pattern(
        string_pattern=f"int(<NON_TERMINAL>) {str(operator.value)} <INTEGER>;",
        instantiated_pattern=ComparisonConstraint(
            operator=operator,
            left=f"int({Pattern.get_id(1)})",
            right=f"{Pattern.get_id(2)}",
            searches={
                Pattern.get_id(1): RuleSearch(NonTerminal("<NON_TERMINAL>")),
                Pattern.get_id(2): RuleSearch(NonTerminal("<INTEGER>")),
            },
            local_variables=predicates.__dict__,
            global_variables=globals(),
        ),
    )

# All Patterns with the form int(<NON_TERMINAL>) <operator> int(<NON_TERMINAL>);
# We exclude GreaterThan and Greater since they can be expressed as LessThan and Less.
for operator in [
    Comparison.EQUAL,
    Comparison.LESS_EQUAL,
    Comparison.LESS,
    Comparison.NOT_EQUAL,
]:
    Pattern(
        string_pattern=f"int(<NON_TERMINAL>) {str(operator.value)} int(<NON_TERMINAL>);",
        instantiated_pattern=ComparisonConstraint(
            operator=operator,
            left=f"int({Pattern.get_id(1)})",
            right=f"int({Pattern.get_id(2)})",
            searches={
                Pattern.get_id(1): RuleSearch(NonTerminal("<NON_TERMINAL>")),
                Pattern.get_id(2): RuleSearch(NonTerminal("<NON_TERMINAL>")),
            },
            local_variables=predicates.__dict__,
            global_variables=globals(),
        ),
    )

Pattern(
    string_pattern="exists <elem> in <NON_TERMINAL>: <elem> in <start>;",
    use_cache=False,
)

Pattern(
    string_pattern="exists <elem> in <NON_TERMINAL>: <elem> in <NON_TERMINAL>;",
    use_cache=False,
)

Pattern(
    string_pattern="exists <elem> in <NON_TERMINAL>: str(<elem>) == <STRING>;",
)

Pattern(
    string_pattern="exists <elem> in <NON_TERMINAL>: <STRING> in <elem>;",
    use_cache=False,
)

# Pattern(
#     string_pattern="""
# def iban_checksum(country: str, bban: str) -> str:
#     moved = bban + country + "00"
#     numeric = "".join(str(int(ch, 36)) for ch in moved)
#     remainder = int(numeric) % 97
#     return 98 - remainder
#
# where iban_checksum(str(<NON_TERMINAL>),str(<NON_TERMINAL>)) == int(<NON_TERMINAL>)
# """
# )

Pattern(
    string_pattern="""
def iban_checksum(iban: str) -> str:
    country = iban[:2]
    bban = iban[4:]
    moved = bban + country + "00"
    numeric = "".join(str(int(ch, 36)) for ch in moved)
    remainder = int(numeric) % 97
    return 98 - remainder

where iban_checksum(str(<NON_TERMINAL>)) == int(<NON_TERMINAL>)
"""
)

Pattern(
    string_pattern="""exists <elem> in <NON_TERMINAL>: (str(<ATTRIBUTE>) == <STRING>) and (int(eval(str(<ATTRIBUTE>))) == <INTEGER>);
    """
)

Pattern(
    string_pattern="exists <elem> in <NON_TERMINAL>: int(eval(str(<elem>))) == <INTEGER>;",
)

Pattern(
    string_pattern="forall <elem> in <NON_TERMINAL>: str(<elem>.<xml_open_tag>.<id>) == str(<elem>.<xml_close_tag>.<id>);",
)