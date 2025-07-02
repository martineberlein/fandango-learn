from copy import deepcopy
from typing import List, Dict, Set, Iterable

from fandango.constraints.base import *
from fandango.language.search import (
    RuleSearch,
    AttributeSearch,
    LengthSearch,
    StarSearch,
)
from fandango.language.symbol import NonTerminal

from fdlearn.data import FandangoInput
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.learning.transformer import ConstraintTransformer
from fdlearn.learning.value_transformer import (
    IntegerPlaceholderTransformer,
    StringPlaceholderTransformer,
)
from fdlearn.learning.value_map import ValueMap, ReachabilityMap


def all_combinations(sequences: list[list]) -> list[list]:
    result = []
    for combo in itertools.product(*sequences):
        result.append(list(combo))
    return result


class PatternProcessor:
    """
    Manages the instantiation of patterns by applying the appropriate PatternInstantiation class.
    """

    def __init__(self, patterns: Iterable[Constraint]):
        self.patterns = patterns

    def instantiate_patterns(
        self,
        relevant_non_terminals: set[NonTerminal],
        positive_inputs: set[FandangoInput],
        value_maps: ValueMap,
        reachability_map: ReachabilityMap = None,
    ) -> set[FandangoConstraintCandidate]:

        transformers = [
            NonTerminalPlaceholderTransformer(
                relevant_non_terminals=relevant_non_terminals,
                reachability_map=reachability_map,
            ),
            IntegerPlaceholderTransformer(
                value_map=value_maps,
                test_inputs=positive_inputs,
            ),
            StringPlaceholderTransformer(
                value_map=value_maps,
                test_inputs=positive_inputs,
            ),
        ]

        final_constraints = self.patterns
        for t in transformers:
            transformed_constraints = []
            for cons in final_constraints:
                constraints = t.transform(constraint=cons)
                transformed_constraints.extend(constraints)
            final_constraints = transformed_constraints

        new_candidates = set()
        for pattern in final_constraints:
            new_candidates.add(FandangoConstraintCandidate(pattern))

        return new_candidates


class NonTerminalPlaceholderTransformer(ConstraintTransformer):
    """
    Visitor that replaces <NON_TERMINAL> and <ATTRIBUTE> placeholders
    in any Constraint. All the “expand over products” logic is
    centralized in `_expand_searches(...)`.
    """

    def __init__(
        self,
        relevant_non_terminals: Set[NonTerminal],
        reachability_map: ReachabilityMap = None,
        limit_descendant_levels: int = 2,
    ):
        """
        Args:
            relevant_non_terminals: NonTerminals used to replace <NON_TERMINAL>.
            reachability_map: for each bound non‐terminal symbol,
                              the set of attribute‐candidates for <ATTRIBUTE>.
        """
        self.relevant_non_terminals: Set[NonTerminal] = relevant_non_terminals
        self.reachability_map: ReachabilityMap = reachability_map
        self.descendant_levels: int = limit_descendant_levels

    def _visit_comparison(
        self,
        constraint: "ComparisonConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["Constraint"]:
        """
        1) Generate all fully‐expanded `searches` dicts via `_expand_searches`.
        2) Rebuild a ComparisonConstraint for each expanded‐searches.
        """
        expanded_search_dicts = self._expand_searches(constraint.searches, bounded_map)

        result: List["Constraint"] = []
        for searches_dict in expanded_search_dicts:
            result.append(
                ComparisonConstraint(
                    operator=constraint.operator,
                    left=constraint.left,
                    right=constraint.right,
                    searches=searches_dict,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
            )
        return result

    def _visit_expression(
        self,
        constraint: "ExpressionConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["Constraint"]:
        """
        Same pattern as ComparisonConstraint, but rebuild ExpressionConstraint.
        """
        expanded_search_dicts = self._expand_searches(constraint.searches, bounded_map)

        result: List["Constraint"] = []
        for searches_dict in expanded_search_dicts:
            result.append(
                ExpressionConstraint(
                    expression=constraint.expression,
                    searches=searches_dict,
                    local_variables=constraint.local_variables,
                    global_variables=constraint.global_variables,
                )
            )
        return result

    def _visit_forall(
        self,
        constraint: "ForallConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["ForallConstraint"]:
        """
        Recurse into the inner statement; then wrap each instantiation
        in a new ForallConstraint, one per relevant non‐terminal.
        """
        if bounded_map is None:
            bounded_map = dict()

        result: List["ForallConstraint"] = []

        is_nt_placeholder = isinstance(
            constraint.search, RuleSearch
        ) and constraint.search.symbol == NonTerminal("<NON_TERMINAL>")

        for candidate_nt in self.relevant_non_terminals:
            if is_nt_placeholder:
                new_search = RuleSearch(candidate_nt)
            else:
                new_search = constraint.search

            # Thread a fresh bounded_map so attributes can see this binding
            new_bounded = {**bounded_map, candidate_nt: constraint.bound}

            # Recurse on the inner statement under new_bounded
            inner_expanded = self.transform(
                constraint.statement, bounded_map=new_bounded
            )
            for inner in inner_expanded:
                result.append(
                    ForallConstraint(
                        statement=inner, bound=constraint.bound, search=new_search
                    )
                )

        return result

    def _visit_exists(
        self,
        constraint: "ExistsConstraint",
        bounded_map=None,
    ) -> List["ExistsConstraint"]:
        """
        If the `search` is a <NON_TERMINAL> placeholder, replace it with each
        relevant non‐terminal. In either case, add (chosen_nt → bound) to the
        new bounded_map before recursing into the inner statement.
        """
        if bounded_map is None:
            bounded_map = dict()

        result: List["ExistsConstraint"] = []

        # Figure out if this ExistsConstraint.search is exactly <NON_TERMINAL>
        is_nt_placeholder = isinstance(
            constraint.search, RuleSearch
        ) and constraint.search.symbol == NonTerminal("<NON_TERMINAL>")

        for candidate_nt in self.relevant_non_terminals:
            if is_nt_placeholder:
                new_search = RuleSearch(candidate_nt)
            else:
                new_search = constraint.search

            # Thread a fresh bounded_map so attributes can see this binding
            new_bounded = {**bounded_map, candidate_nt: constraint.bound}

            # Recurse on the inner statement under new_bounded
            inner_expanded = self.transform(
                constraint.statement, bounded_map=new_bounded
            )
            for inner in inner_expanded:
                result.append(
                    ExistsConstraint(
                        statement=inner, bound=constraint.bound, search=new_search
                    )
                )

        return result

    def _visit_conjunction(
        self,
        constraint: "ConjunctionConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["Constraint"]:
        """
        Expand each sub‐constraint in turn, collect lists of their instantiations,
        take the Cartesian product (all_combinations), and re‐wrap each tuple in
        a ConjunctionConstraint.
        """
        expanded_lists: List[List["Constraint"]] = []
        for sub in constraint.constraints:
            expanded_lists.append(self.transform(sub, bounded_map=bounded_map))

        # all_combinations produces a List[List[Constraint]] of every possible tuple
        all_tuples = all_combinations(expanded_lists)
        return [ConjunctionConstraint(constraints=combo) for combo in all_tuples]

    def _visit_disjunction(
        self,
        constraint: "DisjunctionConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["DisjunctionConstraint"]:
        """
        Expand each sub‐constraint in turn, collect lists of their instantiations,
        take the Cartesian product (all_combinations), and re‐wrap each tuple in
        a ConjunctionConstraint.
        """
        expanded_lists: List[List["Constraint"]] = []
        for sub in constraint.constraints:
            expanded_lists.append(self.transform(sub, bounded_map=bounded_map))

        # all_combinations produces a List[List[Constraint]] of every possible tuple
        all_tuples = all_combinations(expanded_lists)
        return [DisjunctionConstraint(constraints=combo) for combo in all_tuples]

    def _visit_implication(
        self,
        constraint: "ImplicationConstraint",
        bounded_map: Dict[NonTerminal, NonTerminal] = None,
    ) -> List["Constraint"]:
        """
        Recursively expand antecedent and consequent, then combine pairwise.
        """
        expanded_ant = self.transform(constraint.antecedent, bounded_map=bounded_map)
        expanded_con = self.transform(constraint.consequent, bounded_map=bounded_map)

        result: List["Constraint"] = []
        for a in expanded_ant:
            for c in expanded_con:
                result.append(ImplicationConstraint(antecedent=a, consequent=c))
        return result

    def _expand_searches(
        self,
        base_searches: Dict[str, "RuleSearch | AttributeSearch"],
        bounded_map: Dict[NonTerminal, NonTerminal],
    ) -> List[Dict[str, "RuleSearch | AttributeSearch"]]:
        """
        Core placeholder‐expansion helper. Given an initial `base_searches` dict, produce
        a list of *fully‐instantiated* `searches` dicts by:

          1) Replacing all <NON_TERMINAL> placeholders with every combination of
             `self.relevant_non_terminals`.
          2) For each “partially expanded” dict, if any <ATTRIBUTE> placeholders exist,
             loop over each (bound_nt → bound_symbol) in `bounded_map` and over
             `self.reachability_map[bound_nt]` to fill in <ATTRIBUTE>.

        If there are no placeholders of a given type, that stage just yields the input dict unchanged.
        If there are <ATTRIBUTE> placeholders but no valid `(bound_nt, reachable_set)` pairs,
        this will yield an empty list (i.e. no valid expansions).
        """
        # 1) Find keys whose searches[...] is exactly `<NON_TERMINAL>`
        nt_keys = [
            key
            for key, search in base_searches.items()
            if isinstance(search, RuleSearch)
            and search.symbol == NonTerminal("<NON_TERMINAL>")
        ]

        # Build “partially expanded” list by substituting <NON_TERMINAL>
        partials: List[Dict[str, "RuleSearch | AttributeSearch"]] = []
        if nt_keys:
            # For every tuple of replacements (one non‐terminal per nt_key)
            for combo in itertools.product(
                self.relevant_non_terminals, repeat=len(nt_keys)
            ):
                new_searches = deepcopy(base_searches)
                for key, nt_repl in zip(nt_keys, combo):
                    new_searches[key] = RuleSearch(nt_repl)
                partials.append(new_searches)
        else:
            partials.append(deepcopy(base_searches))

        # 2) For each partial, fill in <ATTRIBUTE> if any
        final_expanded: List[
            Dict[str, "RuleSearch | AttributeSearch | DescendantAttributeSearch"]
        ] = []
        for part in partials:
            # Find keys whose searches[...] is `<ATTRIBUTE>`
            attr_keys = [
                key
                for key, search in part.items()
                if isinstance(search, RuleSearch)
                and search.symbol == NonTerminal("<ATTRIBUTE>")
            ]

            if not attr_keys:
                # No <ATTRIBUTE> placeholders → this partial is fully expanded
                final_expanded.append(part)
                continue

            # There *are* <ATTRIBUTE> placeholders; we need at least one (bound_nt → reachable) pair
            any_expanded = False
            for bound_nt, bound_symbol in bounded_map.items():
                reachable = self.reachability_map.get_reachable_non_terminals(bound_nt)
                if not reachable:
                    continue
                for level in range(0, self.descendant_levels):
                    reach = reachable.get(level, ())
                    paths_ = []
                    for r in reach:
                        paths = self.reachability_map.get_all_shortest_paths(
                            bound_nt, r
                        )
                        if not paths:
                            continue
                        paths_.extend(paths)
                    for combo in itertools.product(paths_, repeat=len(attr_keys)):
                        new_searches = deepcopy(part)
                        for key, path in zip(attr_keys, combo):
                            path = path[::-1]
                            tmp_ = RuleSearch(path[0])
                            for nt_ in path[1:-1]:
                                tmp_ = AttributeSearch(RuleSearch(nt_), tmp_)
                            final = AttributeSearch(RuleSearch(bound_symbol), tmp_)
                            print(final)
                            new_searches[key] = final
                        print("New:", new_searches)
                        final_expanded.append(new_searches)
                        any_expanded = True
                    # else:
                    #     for combo in itertools.product(reach, repeat=len(attr_keys)):
                    #         new_searches = deepcopy(part)
                    #         for key, attr_nt in zip(attr_keys, combo):
                    #             # Replace placeholder with AttributeSearch(RuleSearch(bound_symbol), RuleSearch(attr_nt))
                    #             new_searches[key] = DescendantAttributeSearch(RuleSearch(bound_symbol), RuleSearch(attr_nt))
                    #         final_expanded.append(new_searches)
                    #         any_expanded = True

            # If no bound_nt → reachable existed, this partial yields ZERO expansions
            # (i.e. if you had <ATTRIBUTE> but no valid bound_nts, you get no results)
            if not any_expanded:
                # (Intentionally drop this partial entirely—no valid expansions.)
                pass

        final_final_expanded: list[
            dict[str, "RuleSearch | AttributeSearch | LengthSearch"]
        ] = []
        for part in final_expanded:
            length_keys = [
                key
                for key, search in part.items()
                if isinstance(search, LengthSearch)
                and isinstance(search.value, StarSearch)
                and NonTerminal("<NON_TERMINAL>") in search.get_access_points()
            ]

            if not length_keys:
                final_final_expanded.append(part)
                continue

            # For every tuple of replacements (one non‐terminal per nt_key)
            for combo in itertools.product(
                self.relevant_non_terminals, repeat=len(length_keys)
            ):
                new_searches = deepcopy(part)
                for key, nt_repl in zip(length_keys, combo):
                    new_searches[key] = LengthSearch(StarSearch(RuleSearch(nt_repl)))
                final_final_expanded.append(new_searches)

        return final_final_expanded

