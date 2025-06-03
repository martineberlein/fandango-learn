from typing import Optional

from fandango.language.grammar import NonTerminal

from fdlearn.reduction.feature_collector import GrammarFeatureCollector
from fdlearn.reduction.reducer import SHAPRelevanceLearner, FeatureReducer
from fdlearn.data.input import FandangoInput
from fdlearn.learner import FandangoLearner
from fdlearn.logger import LOGGER
from fdlearn.types import OracleType


class FDLearnReducer(FandangoLearner):
    """
    FDLearnReducer extends FandangoLearner to reduce the number of non-terminals that are used to construct
    the diagnoses. It uses SHAPRelevanceLearner to learn the relevant non-terminals.
    """

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
