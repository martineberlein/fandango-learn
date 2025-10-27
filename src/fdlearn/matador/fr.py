from typing import Optional, Union, Iterable

from fandango.language.grammar import NonTerminal, Grammar

from fdlearn.reduction.feature_collector import GrammarFeatureCollector
from fdlearn.reduction.reducer import SHAPRelevanceLearner, FeatureReducer
from fdlearn.data.input import FandangoInput
from fdlearn.logger import LOGGER, LoggerLevel
from fdlearn.refinement.core import HypothesisInputFeatureDebugger, FandangoConstraintCandidate, Generator, FandangoGrammarGenerator, Engine, ParallelEngine
from fdlearn.types import OracleType

from fdlearn.learning.rule_induction.rule_induction import RuleInductionLearner


class RDLearnFR(RuleInductionLearner):

    def __init__(
            self,
            *args,
            oracle: OracleType,
            top_n_relevant_non_terminals: int = 3,
            relevant_non_terminals: set[NonTerminal] | None = None,
            reducer: Optional[FeatureReducer] = None,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.oracle = oracle

        self.learning_inputs: set[FandangoInput] = set()
        self.relevant_non_terminals: set[NonTerminal] | None = relevant_non_terminals

        self.collector = GrammarFeatureCollector(self.grammar)
        self.reducer = reducer or SHAPRelevanceLearner(
            self.grammar, top_n_relevant_features=top_n_relevant_non_terminals
        )

    def set_learning_inputs(self) -> None:
        """
        Generates learning inputs by fuzzing the grammar 100 times.
        Each input is wrapped as a FandangoInput using the provided oracle.
        """
        for _ in range(100):
            tree = self.grammar.fuzz()
            inp = FandangoInput(tree=tree, oracle=self.oracle(str(tree)))
            self.learning_inputs.add(inp)

    def learn_relevant_non_terminals(
            self, test_inputs: set[FandangoInput]
    ) -> set[NonTerminal]:
        """
        Learns the relevant non-terminals from a combination of test inputs and the generated
        learning inputs. It ensures that all inputs have extracted features before applying
        the reducer to determine feature relevance.

        :param test_inputs: A set of FandangoInput objects provided as test inputs.
        :return: A set of non-terminals deemed relevant based on feature analysis.
        """
        if not self.learning_inputs:
            self.set_learning_inputs()

        LOGGER.info("Learning relevant non-terminals.")
        combined_inputs = test_inputs.union(self.learning_inputs)
        for inp in combined_inputs:
            if inp.features is None:
                inp.features = self.collector.collect_features(inp)

        relevant_features = self.reducer.learn(combined_inputs)
        relevant_nonterminals = {feature.non_terminal for feature in relevant_features}
        LOGGER.info("Relevant non-terminals: %s", relevant_nonterminals)
        return relevant_nonterminals

    def get_relevant_non_terminals(
            self, _cached_relevant: set[NonTerminal], test_inputs: set[FandangoInput]
    ) -> set[NonTerminal]:
        """
        Returns the relevant non-terminals. If a cached set is available, it is returned.
        Otherwise, it learns the relevant non-terminals using the provided test inputs.
        The first parameter is unused but required by the superclass signature.

        :param _cached_relevant: Unused cached set of relevant non-terminals.
        :param test_inputs: A set of test FandangoInput objects used for learning if needed.
        :return: A set of relevant non-terminals.
        """
        self.relevant_non_terminals = self.learn_relevant_non_terminals(test_inputs)
        return self.relevant_non_terminals


class Matador(HypothesisInputFeatureDebugger):

    def __init__(
        self,
        grammar: Grammar,
        oracle: OracleType,
        initial_inputs: Union[Iterable[str], Iterable[FandangoInput]],
        max_iterations: int = 10,
        timeout_seconds: int = 3600,
        learner: Optional[RuleInductionLearner] = None,
        generator: Optional[Generator] = None,
        top_n_relevant_non_terminals: int = 3,
        logger_level: LoggerLevel = LoggerLevel.INFO,
        **kwargs,
    ):
        learner: RuleInductionLearner = (
            learner
            if learner
            else RDLearnFR(
                grammar,
                oracle=oracle,
                top_n_relevant_non_terminals=top_n_relevant_non_terminals,
                logger_level=logger_level,
            )
        )
        generator: Generator = (
            generator if generator else FandangoGrammarGenerator(grammar)
        )
        self.engine: Engine = ParallelEngine(generator)

        super().__init__(
            grammar,
            oracle,
            initial_inputs,
            learner=learner,
            generator=generator,
            timeout_seconds=timeout_seconds,
            max_iterations=max_iterations,
            logger_level=logger_level,
            **kwargs,
        )
        self.max_candidates = 5

    def learn_candidates(
        self, test_inputs: set[FandangoInput]
    ) -> Optional[list[FandangoConstraintCandidate]]:
        """
        Learn the candidates based on the test inputs. The candidates are ordered based on their scores.
        :param test_inputs: The test inputs to learn the candidates from.
        :return Optional[List[Candidate]]: The learned candidates.
        """
        LOGGER.info("Learning the candidates.")

        inv = self.learner.learn_constraints(
            test_inputs,
        )
        print(inv)
        return inv

    def generate_test_inputs(
        self, candidates: list[FandangoConstraintCandidate]
    ) -> set[FandangoInput]:
        """
        Generate the test inputs based on the learned candidates.
        :param candidates: The learned candidates.
        :return Set[Input]: The generated test inputs.
        """
        LOGGER.info(f"Generating new test inputs for {len(candidates)} candidates.")
        test_inputs = self.engine.generate(candidates=candidates)
        return test_inputs

    def run_test_inputs(self, test_inputs: set[FandangoInput]) -> set[FandangoInput]:
        """
        Run the test inputs to label them. The test inputs are labeled based on the oracle.
        Feature vectors are assigned to the test inputs.
        :param test_inputs: The test inputs to run.
        :return Set[Input]: The labeled test inputs.
        """
        LOGGER.info(f"Running {len(test_inputs)} test inputs.")
        labeled_test_inputs = self.runner.label(test_inputs=test_inputs)
        return labeled_test_inputs
