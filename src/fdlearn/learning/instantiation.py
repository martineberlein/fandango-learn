from copy import deepcopy
from typing import List, Dict, Set, Iterable, Tuple, Callable, Mapping

from fandango.constraints.base import *
from fandango.language.search import (
    RuleSearch,
    AttributeSearch,
    Container,
    LengthSearch,
    StarSearch,
    DescendantAttributeSearch,
)
from fandango.language.symbol import NonTerminal

from fdlearn.data import FandangoInput
from fdlearn.learning.candidate import FandangoConstraintCandidate
from fdlearn.learning.transformer import ConstraintTransformer
from fdlearn.logger import LOGGER
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
        **kwargs,
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


class ValuePlaceholderTransformer(ConstraintVisitor, ABC):
    """
    A visitor for replacing placeholders like <STRING> or <INTEGER> in constraints with actual values.
    """

    def __init__(
        self,
        value_maps: ValueMap,
        test_inputs: Set[FandangoInput],
    ):
        """
        Initialize the transformer with value maps for placeholders.

        Args:
            value_maps (Dict[str, Dict[NonTerminal, List[str]]]): Mapping of placeholders to their replacement values.
        """
        super().__init__()
        self.value_maps: ValueMap = value_maps
        self.results: List[Constraint] = []
        self.test_inputs: Set[FandangoInput] = test_inputs

        self.bounded_non_terminals: dict[NonTerminal, NonTerminal] = dict()

    def reset(self):
        """
        Reset the results and bounded non-terminals for a new transformation.
        """
        self.results = []
        self.bounded_non_terminals = dict()

    def do_continue(self, constraint: "Constraint") -> bool:
        return False

    @abstractmethod
    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """ """
        raise NotImplementedError()

    @abstractmethod
    def remove_value_map(self, bound: NonTerminal):
        raise NotImplementedError()

    @abstractmethod
    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """
        Replace placeholders in a ComparisonConstraint with corresponding values.
        """
        raise NotImplementedError()

    def visit_forall_constraint(self, constraint: "ForallConstraint"):
        """
        Recursively visit the statement inside a ForallConstraint.
        """
        assert isinstance(
            constraint.search, RuleSearch
        ), f"AttributeSearch not yet supported! {constraint}"

        self.update_value_map(constraint.bound, constraint.search)
        constraint.statement.accept(self)
        self.remove_value_map(constraint.bound)
        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ForallConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    @staticmethod
    def get_search_symbol(search: NonTerminalSearch) -> NonTerminal:
        """
        Return the symbol corresponding to the given search instance.
        :param search:
        :return:
        """
        assert isinstance(search, RuleSearch) or isinstance(search, AttributeSearch)
        symbol = search.get_access_points()
        return symbol[0]

    def visit_exists_constraint(self, constraint: "ExistsConstraint"):
        """
        Recursively visit the statement inside an ExistsConstraint.
        """
        assert isinstance(
            constraint.search, RuleSearch
        ), f"AttributeSearch not yet supported! {constraint}"

        self.update_value_map(constraint.bound, constraint.search)
        # self.bounded_non_terminals[constraint.bound] = constraint.search.symbol
        self.bounded_non_terminals[constraint.bound] = self.get_search_symbol(
            constraint.search
        )
        constraint.statement.accept(self)
        self.remove_value_map(constraint.bound)

        del self.bounded_non_terminals[constraint.bound]

        transformed_constraints = self.results
        self.results = []  # Reset for independent processing

        for transformed_statement in transformed_constraints:
            self.results.append(
                ExistsConstraint(
                    statement=transformed_statement,
                    bound=constraint.bound,
                    search=constraint.search,
                )
            )

    def visit_disjunction_constraint(self, constraint: "DisjunctionConstraint"):
        """
        Recursively visit each constraint in a DisjunctionConstraint.
        """
        all_transformed_constraints = []
        for sub_constraint in constraint.constraints:
            sub_constraint.accept(self)
            all_transformed_constraints.extend(self.results)
            self.results = []  # Reset after each sub-constraint

        self.results.append(
            DisjunctionConstraint(constraints=all_transformed_constraints)
        )

    def visit_conjunction_constraint(self, constraint: "ConjunctionConstraint"):
        """
        Recursively visit each constraint in a ConjunctionConstraint.
        """
        all_transformed_constraints: list[list] = list()
        for sub_constraint in constraint.constraints:
            sub_constraint.accept(self)
            all_transformed_constraints.append(self.results)
            self.results = []  # Reset after each sub-constraint

        all_conjunctions = all_combinations(all_transformed_constraints)

        for conjunction in all_conjunctions:
            self.results.append(ConjunctionConstraint(constraints=conjunction))

    def visit_implication_constraint(self, constraint: "ImplicationConstraint"):
        """
        Recursively visit the antecedent and consequent in an ImplicationConstraint.
        """
        constraint.antecedent.accept(self)
        transformed_antecedents = self.results
        self.results = []  # Reset after antecedent

        constraint.consequent.accept(self)
        transformed_consequents = self.results
        self.results = []  # Reset after consequent

        for antecedent in transformed_antecedents:
            for consequent in transformed_consequents:
                self.results.append(
                    ImplicationConstraint(antecedent=antecedent, consequent=consequent)
                )

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):
        """
        Expression constraints are returned as-is.
        """
        self.results.append(constraint)

    @staticmethod
    def get_combinations(
        constraint: Constraint,
        tree: DerivationTree,
        scope: Optional[Dict[NonTerminal, DerivationTree]] = None,
    ):
        nodes: List[List[Tuple[str, Container]]] = []
        for name, search in constraint.searches.items():
            if isinstance(search, RuleSearch) and search.symbol == NonTerminal(
                "<INTEGER>"
            ):
                continue
            nodes.append(
                [(name, container) for container in search.find(tree, scope=scope)]
            )
        return itertools.product(*nodes)

    def evaluate_partial(self, constraint: "ComparisonConstraint"):
        """This function is used to evaluate the partial constraints"""
        results = set()

        try:
            tmp_constraint = deepcopy(constraint)
        except TypeError as e:
            return set()
        for name, search in tmp_constraint.searches.items():
            if isinstance(search, AttributeSearch):
                search.base = RuleSearch(self.bounded_non_terminals[search.base.symbol])
            elif (
                isinstance(search, RuleSearch)
                and search.symbol
                not in (NonTerminal("<INTEGER>"), NonTerminal("<STRING>"))
                and self.bounded_non_terminals[search.symbol]
            ):
                search.symbol = self.bounded_non_terminals[search.symbol]

        for inp in self.test_inputs:
            scope = None
            for combination in self.get_combinations(tmp_constraint, inp.tree, scope):
                local_variables = tmp_constraint.local_variables.copy()
                local_variables.update(
                    {name: container.evaluate() for name, container in combination}
                )
                try:
                    left_result = eval(
                        tmp_constraint.left,
                        tmp_constraint.global_variables,
                        local_variables,
                    )
                    results.add(str(left_result))
                except Exception as e:
                    e.add_note("Evaluation failed: " + constraint.left)
                    LOGGER.debug(e)
                    continue
        return results

    def replace_placeholders(
        self,
        initialized_patterns: List[Tuple[Constraint, Set[NonTerminal]]],
        placeholder: NonTerminal,
        values: Dict[NonTerminal, Set[str | int | float]],
        format_value: Callable[[str], str],
    ) -> List[Tuple[Constraint, Set[NonTerminal]]]:
        """
        Replaces placeholders like <STRING> or <INTEGER> with actual values.

        Args:
            initialized_patterns (List[Tuple[Constraint, Set[NonTerminal]]]): Patterns with placeholders.
            placeholder (NonTerminal): The placeholder symbol to replace.
            values (Dict[NonTerminal, List[str]]): Values to replace the placeholder with.
            format_value (Callable[[str], str]): A function to format the replacement value.

        Returns:
            List[Tuple[Constraint, Set[NonTerminal]]]: Updated patterns with replaced placeholders.
        """
        new_patterns = []
        for pattern, non_terminals in initialized_patterns:
            matches = []
            for name, search in pattern.searches.items():
                if isinstance(search, RuleSearch):
                    if search.symbol == placeholder:
                        matches.append(name)

            non_terminals = set()
            for name, search in pattern.searches.items():
                if isinstance(search, RuleSearch):
                    if search not in matches and search.symbol != placeholder:
                        non_terminals.add(search.symbol)
                elif isinstance(search, AttributeSearch):
                    if search not in matches:
                        non_terminals.add(search.attribute.symbol)

            if matches:
                if isinstance(pattern, ComparisonConstraint):
                    for non_terminal in non_terminals:
                        vals = set(values.get(non_terminal, []))
                        vals.update(self.evaluate_partial(pattern))

                        for value in vals:
                            updated_right = pattern.right
                            for match in matches:
                                updated_right = updated_right.replace(
                                    match, format_value(value), 1
                                )
                            new_searches = deepcopy(pattern.searches)
                            for match in matches:
                                del new_searches[match]
                            new_pattern = ComparisonConstraint(
                                operator=pattern.operator,
                                left=pattern.left,
                                right=updated_right,
                                searches=new_searches,
                                local_variables=pattern.local_variables,
                                global_variables=pattern.global_variables,
                            )
                            new_patterns.append((new_pattern, non_terminals))
                else:
                    raise ValueError(
                        f"Only comparison constraints are supported. "
                        f"Constraint type {type(pattern)} is not yet supported."
                    )
            else:
                new_patterns.append((pattern, non_terminals))

        return new_patterns


class IntegerValuePlaceholderTransformer(ValuePlaceholderTransformer):

    def __init__(self, value_maps: ValueMap, test_inputs: Set[FandangoInput]):
        super().__init__(value_maps, test_inputs)

    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """ """
        if search.symbol in self.value_maps.numeric_values:
            self.value_maps.numeric_values[bound] = self.value_maps.numeric_values[
                search.symbol
            ]

    def remove_value_map(self, bound: NonTerminal):
        if bound in self.value_maps.numeric_values:
            del self.value_maps.numeric_values[bound]

    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """
        Replace placeholders in a ComparisonConstraint with corresponding values.
        :param constraint:
        :return:
        """

        instantiated_patterns = [(constraint, set())]
        # Replace <INTEGER> placeholders
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<INTEGER>"),
            values=self.value_maps.filtered_numeric_values,
            format_value=lambda x: f"{int(x)}",
        )

        self.results.extend([pattern for pattern, _ in instantiated_patterns])


class StringValuePlaceholderTransformer(ValuePlaceholderTransformer):

    def __init__(self, value_maps: ValueMap, test_inputs: Set[FandangoInput]):
        super().__init__(value_maps, test_inputs)

    def update_value_map(self, bound: NonTerminal, search: RuleSearch):
        """ """
        if search.symbol in self.value_maps.string_values:
            self.value_maps.string_values[bound] = self.value_maps.string_values[
                search.symbol
            ]

    def remove_value_map(self, bound: NonTerminal):
        if bound in self.value_maps.string_values:
            del self.value_maps.string_values[bound]

    def visit_comparison_constraint(self, constraint: "ComparisonConstraint"):
        """
        Replace placeholders in a ComparisonConstraint with corresponding values.
        :param constraint:
        :return:
        """
        instantiated_patterns = [(constraint, set())]
        # Replace <STRING> placeholders
        instantiated_patterns = self.replace_placeholders(
            instantiated_patterns,
            NonTerminal("<STRING>"),
            values=self.value_maps.string_values,
            format_value=lambda x: f"'{x}'",
        )

        self.results.extend([pattern for pattern, _ in instantiated_patterns])

    @staticmethod
    def escape_string(s):
        return s.encode("unicode_escape").decode("utf-8")

    def visit_expression_constraint(self, constraint: "ExpressionConstraint"):

        new_patterns = []

        matches = [
            key
            for key in constraint.searches.keys()
            if constraint.searches[key].symbol == NonTerminal("<STRING>")
        ]

        non_terminals = {
            constraint.searches[key].symbol
            for key in constraint.searches.keys()
            if key not in matches
        }

        if matches:
            for non_terminal in non_terminals:
                values = set(self.value_maps.string_values[non_terminal])

                for value in values:
                    new_expression = constraint.expression
                    for match in matches:
                        new_expression = new_expression.replace(
                            match, "'" + self.escape_string(str(value)) + "'", 1
                        )
                    new_searches = deepcopy(constraint.searches)
                    for match in matches:
                        del new_searches[match]
                    new_pattern = ExpressionConstraint(
                        expression=new_expression,
                        searches=new_searches,
                        local_variables=constraint.local_variables,
                        global_variables=constraint.global_variables,
                    )
                    new_patterns.append(new_pattern)
        else:
            new_patterns.append(constraint)
        self.results.extend(new_patterns)
