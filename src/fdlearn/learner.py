from typing import List, Iterable, Optional, Set, Callable
import os
import contextlib

from fandango.language.grammar import Grammar
from fandango.language.symbol import NonTerminal

from .learning.candidate import FandangoConstraintCandidate
from .data import FandangoInput, OracleResult
from .logger import LOGGER, LoggerLevel
from .learning.combination import ConjunctionProcessor, DisjunctionProcessor
from .learning.instantiation import PatternProcessor, ValueMaps
from .core import BaseFandangoLearner
from .types import OracleType


class FandangoLearner(BaseFandangoLearner):
    """
    A candidate learner that learns fandango constraints based on patterns from a pattern repository.
    """

    def __init__(
        self,
        grammar: Grammar,
        patterns: Optional[Iterable[str]] = None,
        logger_level: LoggerLevel = LoggerLevel.INFO,
        max_conjunction_size=2,
        use_all_non_terminals=False,
        **kwargs,
    ):
        """
        Initializes the FandangoLearner with a grammar and optional patterns.

        Args:
            grammar (Grammar): The grammar used for parsing and learning constraints.
            patterns (Optional[Iterable[str]]): A collection of patterns to be used in the learning process.
            **kwargs: Additional arguments for customization.
        """

        if logger_level is not None:
            LOGGER.setLevel(logger_level.value)

        super().__init__(grammar, patterns, **kwargs)
        self.max_conjunction_size = max_conjunction_size
        self.max_disjunction_size = 2
        self.positive_learning_size = 5
        self.use_all_non_terminals = use_all_non_terminals

        self.pattern_processor = PatternProcessor(self.patterns)

        self.conjunction_processor = ConjunctionProcessor(
            self.max_conjunction_size, self.min_precision, self.min_recall
        )
        self.disjunction_processor = DisjunctionProcessor(
            self.max_disjunction_size, self.min_precision, self.min_recall
        )

        # Refinement
        self.all_positive_inputs = set()
        self.all_negative_inputs = set()
        self.removed_candidates = set()

    def learn_constraints(
        self,
        test_inputs: set[FandangoInput] | set[str],
        relevant_non_terminals: Set[NonTerminal] = None,
        oracle: OracleType = None,
        **kwargs,
    ) -> Optional[List[FandangoConstraintCandidate]]:
        """
        Learns constraints based on the provided test inputs and grammar patterns.

        Args:
            test_inputs (Set[FandangoInput]): A set of test inputs used for learning constraints.
            relevant_non_terminals (Set[NonTerminal], optional): A set of non-terminals relevant for learning.
            oracle (OracleType, optional): An oracle function to evaluate inputs.
            **kwargs: Additional arguments for learning customization.

        Returns:
            Optional[List[FandangoConstraintCandidate]]: A list of learned constraint candidates or None.
        """
        if any(isinstance(inp, str) for inp in test_inputs):
            test_inputs = self.parse_string_initial_inputs(test_inputs, oracle)

        relevant_non_terminals = self.get_relevant_non_terminals(
            relevant_non_terminals, test_inputs
        )

        positive_inputs, negative_inputs = self.categorize_inputs(test_inputs)
        self.update_inputs(positive_inputs, negative_inputs)

        sorted_positive_inputs = self.sort_and_filter_positive_inputs(
            self.all_positive_inputs
        )

        value_maps = ValueMaps(relevant_non_terminals)
        value_maps.extract_non_terminal_values(self.all_positive_inputs)

        instantiated_candidates = self.pattern_processor.instantiate_patterns(
            relevant_non_terminals, sorted_positive_inputs, value_maps=value_maps
        )

        candidates_to_evaluate: List[FandangoConstraintCandidate] = (
            [] + self.candidates.candidates
        )
        for candidate in instantiated_candidates - self.removed_candidates:
            if candidate not in self.candidates:
                candidates_to_evaluate.append(candidate)

        LOGGER.info("Evaluating %s candidates", len(candidates_to_evaluate))
        self.validate_and_add_new_candidates(
            candidates_to_evaluate, positive_inputs, negative_inputs
        )

        LOGGER.info(f"Calculating combinations for {len(self.candidates)} candidates")
        conjunction_candidates = self.conjunction_processor.process(self.candidates)
        for candidate in conjunction_candidates:
            self.candidates.append(candidate)

        # disjunction_candidates = self.disjunction_processor.process(self.candidates)
        # for candidate in disjunction_candidates:
        #     self.candidates.append(candidate)

        results = self.get_best_candidates()
        LOGGER.info(f"Learned {len(results)} constraint(s) that meet(s) the criteria")

        return results

    def parse_string_initial_inputs(
        self, initial_inputs: Set[str], oracle: Callable[[str], OracleResult]
    ) -> Set[FandangoInput]:
        """
        Parses string inputs and generates FandangoInput objects.

        Args:
            initial_inputs (Set[str]): A set of string inputs.
            oracle (Callable[[str], OracleResult]): An oracle function to evaluate inputs.

        Returns:
            Set[FandangoInput]: A set of FandangoInput objects.
        """
        return {
            FandangoInput.from_str(self.grammar, inp, oracle=oracle(inp))
            for inp in initial_inputs
        }

    def sort_and_filter_positive_inputs(
        self, positive_inputs: Set[FandangoInput]
    ) -> Set[FandangoInput]:
        """
        Filters and sorts positive inputs for learning.

        Args:
            positive_inputs (Set[FandangoInput]): A set of positive inputs.

        Returns:
            Set[FandangoInput]: A filtered subset of positive inputs.
        """
        filtered_inputs = set(list(positive_inputs)[: self.positive_learning_size])
        LOGGER.info("Filtered positive inputs for learning: %s", len(filtered_inputs))
        return filtered_inputs

    def update_inputs(
        self, positive_inputs: Set[FandangoInput], negative_inputs: Set[FandangoInput]
    ):
        self.all_positive_inputs.update(positive_inputs)
        self.all_negative_inputs.update(negative_inputs)

    def validate_and_add_new_candidates(
        self,
        candidates: List[FandangoConstraintCandidate],
        positive_inputs: Set[FandangoInput],
        negative_inputs: Set[FandangoInput],
    ) -> None:
        """
        Generates constraint candidates based on instantiated patterns and evaluates them.

        Args:
            candidates (Set[FandangoConstraintCandidate]): A set of new candidates.
            positive_inputs (Set[FandangoInput]): A set of positive inputs.
            negative_inputs (Set[FandangoInput]): A set of negative inputs.
        """
        for candidate in candidates:
            if candidate not in self.candidates:
                if self.evaluate_candidate(
                    candidate, self.all_positive_inputs, self.all_negative_inputs
                ):
                    self.candidates.append(candidate)
                    LOGGER.debug("Added new candidate: %s", candidate)
                else:
                    self.removed_candidates.add(candidate)
            else:
                if not self.evaluate_candidate(
                    candidate, positive_inputs, negative_inputs
                ):
                    self.candidates.remove(candidate)
                    self.removed_candidates.add(candidate)

    def evaluate_candidate(
        self, candidate: FandangoConstraintCandidate, positive_inputs, negative_inputs
    ):
        """
        Evaluates a candidate against positive and negative inputs.
        This method checks if the candidate is valid by evaluating its recall and specificity.

        Args:
            candidate (FandangoConstraintCandidate): The candidate to evaluate.
            positive_inputs (Set[FandangoInput]): A set of positive inputs.
            negative_inputs (Set[FandangoInput]): A set of negative inputs.

        Returns:
            bool: True if the candidate is valid, False otherwise.
        """
        try:
            # Redirect sys.stderr to a null file during the call, Fandango allways prints to stderr
            with open(os.devnull, "w") as null_file, contextlib.redirect_stderr(null_file):
                candidate.evaluate(positive_inputs)
                if candidate.recall() >= self.min_recall:
                    candidate.evaluate(negative_inputs)
                    return True
        except Exception as e:
            LOGGER.debug(
                "Error when evaluation candidate %s: %s", candidate.constraint, e
            )
        return False

    def filter_candidates(self):
        """
        Filters candidates based on their specificity and recall.
        Candidates with specificity or recall below the defined thresholds are removed.
        This method is called after the learning process to refine the candidate set.
        """
        candidates_to_remove = [
            candidate
            for candidate in self.candidates
            if candidate.specificity() < self.min_precision
            or candidate.recall() < self.min_recall
        ]
        LOGGER.debug("Removing candidates: %s", len(candidates_to_remove))

        for candidate in candidates_to_remove:
            self.candidates.remove(candidate)

    def get_relevant_non_terminals(
        self, relevant_non_terminals: set[NonTerminal], test_inputs: set[FandangoInput]
    ) -> set[NonTerminal]:
        """
        Get the relevant non-terminals for the learning process.
        If no relevant non-terminals are provided, extract them from the test inputs.
        If use_all_non_terminals is set to True, all non-terminals in the grammar are used.

        Args:
            relevant_non_terminals (set[NonTerminal]): A set of relevant non-terminals.
            test_inputs (set[FandangoInput]): A set of test inputs.

        Returns:
            set[NonTerminal]: A set of relevant non-terminals.
        """
        if not relevant_non_terminals:
            if self.use_all_non_terminals:
                relevant_non_terminals = set(self.grammar)
            else:
                relevant_non_terminals = self.extract_non_terminals_from_trees(
                    test_inputs
                )
        return relevant_non_terminals

    @staticmethod
    def extract_non_terminals_from_trees(
        test_inputs: Iterable[FandangoInput],
    ) -> Set[NonTerminal]:
        """
        Extracts non-terminals from the provided trees.

        Args:
            test_inputs (Iterable[FandangoInput]): An iterable of FandangoInput objects.

        Returns:
            Set[NonTerminal]: A set of extracted non-terminals.
        """
        non_terminals = set()
        for inp in test_inputs:
            if inp.oracle.is_failing():
                tree = inp.tree
                non_terminals.update(tree.get_non_terminal_symbols())

        return non_terminals
