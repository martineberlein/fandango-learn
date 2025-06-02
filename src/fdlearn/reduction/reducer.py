import logging
from typing import List, Set, Type, Optional, Any, Tuple
from abc import ABC, abstractmethod
import numpy as np
from pandas import DataFrame
from lightgbm import LGBMClassifier
from sklearn import preprocessing
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from shap import TreeExplainer, summary_plot

from fandango.language.grammar import Grammar, NonTerminal

from fdlearn.data import FandangoInput, OracleResult
from fdlearn.logger import LOGGER
from fdlearn.reduction.feature_class import get_reachability_map
from fdlearn.reduction.feature_collector import (
    Feature,
    FeatureFactory,
    DEFAULT_FEATURE_TYPES,
)


MAX_CORRELATED_FEATURES: int = 10


class FeatureReducer(ABC):
    """
    A feature reducer is responsible for extracting the feature that are most relevant for the program failure.
    """

    def __init__(
        self,
        grammar: Grammar,
        feature_types: Optional[List[Type[Feature]]] = None,
    ):
        self.grammar = grammar
        self.features = FeatureFactory(self.grammar).build(
            feature_types or DEFAULT_FEATURE_TYPES
        )

    @abstractmethod
    def learn(self, test_inputs: Set[FandangoInput]) -> Set[Feature]:
        """
        Get the relevant features for the program failure.
        """
        raise NotImplementedError()


class RelevanceFeatureReducer(FeatureReducer, ABC):

    def learn(self, test_inputs: Set[FandangoInput]) -> Set[Feature]:
        """
        Get the relevant features for the program failure.
        """
        x_train, y_train = self.construct_learning_data(test_inputs)
        return self.get_relevant_features(test_inputs, x_train, y_train)

    @abstractmethod
    def get_relevant_features(
        self, test_inputs: Set[FandangoInput], x_train: DataFrame, y_train: List[int]
    ) -> Set[Feature]:
        """
        Get the relevant features for the program failure.
        """
        raise NotImplementedError()

    @staticmethod
    def filter_test_inputs(test_inputs: Set[FandangoInput]) -> List[FandangoInput]:
        """
        Filter out inputs with undefined oracle results.
        """
        return [inp for inp in test_inputs if inp.oracle != OracleResult.UNDEFINED]

    def construct_records(self, filtered_inputs: List[FandangoInput]) -> List[dict]:
        """
        Construct records (list of dictionaries) for the DataFrame from filtered inputs.
        """
        return [
            {
                feature: inp.features.get_feature_value(feature)
                for feature in self.features
            }
            for inp in filtered_inputs
        ]

    @staticmethod
    def construct_labels(filtered_inputs: List[FandangoInput]) -> List[int]:
        """
        Construct labels based on whether the inputs are failing.
        """
        return [int(inp.oracle.is_failing()) for inp in filtered_inputs]

    @staticmethod
    def clean_dataframe(df: DataFrame) -> DataFrame:
        """
        Clean the DataFrame by replacing -inf with a sentinel value and dropping columns
        with only one unique value.
        """
        df = df.replace(-np.inf, np.nan)
        # df = DataFrame.from_records(records).replace(-np.inf, -(2**32))
        return df.drop(columns=df.columns[df.nunique() == 1])

    def construct_learning_data(
        self, test_inputs: Set[FandangoInput]
    ) -> Tuple[DataFrame, List[int]]:
        """
        Construct the learning data for the relevant features.
        """
        if not test_inputs:
            return DataFrame(), []

        filtered_inputs = self.filter_test_inputs(test_inputs)

        if not filtered_inputs:
            return DataFrame(), []

        records = self.construct_records(filtered_inputs)
        labels = self.construct_labels(filtered_inputs)

        df = DataFrame.from_records(records)
        df = self.clean_dataframe(df)

        return df, labels


class CorrelationRelevanceFeatureLearner(RelevanceFeatureReducer, ABC):
    """
    A feature relevance learner that uses correlation to determine the most relevant features for the program failure.
    """

    def __init__(
        self,
        grammar: Grammar,
        feature_types: Optional[List[Type[Feature]]] = None,
        top_n_relevant_features: int = 3,
        correlation_threshold: float = 0.7,
        prune_parent_correlation: bool = False,
        add_correlating_features: bool = True,
    ):
        super().__init__(grammar, feature_types)
        self.correlation_threshold = correlation_threshold
        self.reachability_map = get_reachability_map(grammar)
        self.prune_parent_correlation = prune_parent_correlation
        self.top_n_relevant_features = top_n_relevant_features
        self.add_correlating_features = add_correlating_features

    def learn(self, test_inputs: Set[FandangoInput]) -> Set[Feature]:
        """
        Get the relevant features for the program failure.
        """
        x_train, y_train = self.construct_learning_data(test_inputs)
        relevant_features: Set[Feature] = self.get_relevant_features(
            test_inputs, x_train, y_train
        )
        relevant_features = {
            feature
            for feature in relevant_features
            if feature.non_terminal != NonTerminal("<start>")
        }
        if self.add_correlating_features:
            correlated_features: Set[Feature] = self.find_correlated_features(
                x_train, relevant_features
            )
            relevant_features.update(correlated_features)

        return relevant_features

    def find_correlated_features(
        self, x_train: DataFrame, relevant_features: Set[Feature]
    ) -> Set[Feature]:
        """
        Find the correlated features based on the primary features.
        """
        correlation_matrix = x_train.corr(method="spearman")
        correlated_features = set()

        for primary in relevant_features:
            for feature, value in correlation_matrix[primary].items():
                if abs(value) > self.correlation_threshold:
                    if self.is_correlating_feature_valid(primary, feature):
                        correlated_features.add(feature)

        correlated_features = set(list(correlated_features)[:MAX_CORRELATED_FEATURES])
        LOGGER.debug(f"Added Features: {correlated_features} due to high correlation.")
        return correlated_features

    def is_correlating_feature_valid(
        self, primary_feature: Feature, correlating_feature: Feature
    ) -> bool:
        """
        Determine if a correlating feature should be considered valid based on graph reachability
        and other criteria.
        """
        # We could also just check for the non_terminal, but this is more explicit.
        # We don't want to correlate the same feature with itself. But len(<function>) or exists(<function>->"sqrt")
        # is a valid correlation and helps with the learning process.
        if primary_feature == correlating_feature:
            return False

        if correlating_feature.non_terminal == NonTerminal("<start>"):
            return False

        if not self.prune_parent_correlation:
            return True

        # If the primary feature is reachable from the correlating feature, but not vice versa, then the
        # correlating feature is a parent of the primary feature. We don't want to correlate parents with children
        # as this can lead to overfitting.
        if (
            correlating_feature.non_terminal
            in self.reachability_map[primary_feature.non_terminal]
            and primary_feature.non_terminal
            not in self.reachability_map[correlating_feature.non_terminal]
        ):
            # print(f"Primary: {primary_feature.non_terminal} Correlating: {correlating_feature.non_terminal}")
            return False

        return True


class SKLearFeatureRelevanceLearner(CorrelationRelevanceFeatureLearner, ABC):
    """
    A feature relevance learner that uses scikit-learn classifiers to determine the most relevant features.
    """

    threshold = 0.1

    def get_features(self, x_train: DataFrame, classifier) -> List[Feature]:
        """
        Get the most important features from the classifier based on the threshold and top_n.
        """
        features_with_importance = list(
            zip(x_train.columns, classifier.feature_importances_)
        )

        sorted_features = sorted(
            features_with_importance, key=lambda x: x[1], reverse=True
        )
        important_features = [
            feature
            for feature, importance in sorted_features
            if importance >= self.threshold
        ][: self.top_n_relevant_features]

        return important_features

    @abstractmethod
    def fit(self, x_train: DataFrame, y_train: List[int]) -> Any:
        """
        Fit the classifier to the training data.
        """
        raise NotImplementedError()

    def get_relevant_features(
        self, test_inputs: Set[FandangoInput], x_train: DataFrame, y_train: List[int]
    ) -> Set[Feature]:
        """
        Get the relevant features for the program failure based on the classifier.
        """
        classifier = self.fit(x_train, y_train)
        return set(self.get_features(x_train, classifier))


class DecisionTreeRelevanceLearner(SKLearFeatureRelevanceLearner):
    """
    A feature relevance learner that uses a decision tree classifier to determine the most relevant features
    for the program failure.
    """

    def fit(self, x_train: DataFrame, y_train: List[int]) -> Any:
        """
        Fit the decision tree classifier to the training data.
        """
        classifier = DecisionTreeClassifier(random_state=0)
        classifier.fit(x_train, y_train)
        return classifier


class RandomForestRelevanceLearner(SKLearFeatureRelevanceLearner):
    """
    A feature relevance learner that uses a random forest classifier to determine the most relevant features
    for the program failure.
    """

    def fit(self, x_train: DataFrame, y_train: List[int]) -> Any:
        """
        Fit the random forest classifier to the training data.
        """
        classifier = RandomForestClassifier(n_estimators=10, random_state=0)
        classifier.fit(x_train, y_train)
        return classifier


class GradientBoostingTreeRelevanceLearner(SKLearFeatureRelevanceLearner):
    """
    A feature relevance learner that uses a gradient boosting tree classifier to determine the most relevant features
    for the program failure.
    """

    def fit(self, x_train: DataFrame, y_train: List[int]) -> Any:
        """
        Fit the gradient boosting tree classifier to the training data.
        """
        classifier = LGBMClassifier(
            max_depth=5, n_estimators=100, objective="binary", verbose=-1
        )
        classifier.fit(x_train, y_train)
        return classifier


class SHAPRelevanceLearner(CorrelationRelevanceFeatureLearner):
    """
    A feature relevance learner that uses SHAP values to determine the most relevant features for the program failure.
    """

    def __init__(
        self,
        grammar: Grammar,
        top_n_relevant_features: int = 3,
        feature_types: Optional[List[Type[Feature]]] = None,
        classifier_type: Optional[
            Type[SKLearFeatureRelevanceLearner]
        ] = GradientBoostingTreeRelevanceLearner,
        normalize_data: bool = False,
        show_beeswarm_plot: bool = False,
        **kwargs,
    ):
        super().__init__(
            grammar,
            top_n_relevant_features=top_n_relevant_features,
            feature_types=feature_types,
            **kwargs,
        )
        self.classifier = classifier_type(self.grammar)
        self.show_beeswarm_plot = show_beeswarm_plot
        self.normalize_data = normalize_data

    def get_relevant_features(
        self, test_inputs: Set[FandangoInput], x_train: DataFrame, y_train: List[int]
    ) -> Set[Feature]:
        """
        Get the relevant features for the program failure based on SHAP values.
        """
        x_train_normalized = self.normalize_learning_data(x_train)
        classifier = self.classifier.fit(x_train_normalized, y_train)
        shap_values: np.ndarray = self.get_shap_values(classifier, x_train)
        if self.show_beeswarm_plot:
            self.display_beeswarm_plot(shap_values, x_train)
        return set(
            self.get_sorted_features_by_importance(shap_values, x_train)[
                : self.top_n_relevant_features
            ]
        )

    def normalize_learning_data(self, data: DataFrame):
        """
        Normalize the learning data if necessary.
        """
        if self.normalize_data:
            normalized = preprocessing.MinMaxScaler().fit_transform(data)
            return DataFrame(normalized, columns=data.columns)
        else:
            return data

    @staticmethod
    def get_shap_values(classifier, x_train) -> np.ndarray:
        explainer = TreeExplainer(classifier)
        shap_values = explainer.shap_values(x_train, from_call=True)

        # For binary classification, shap_values will be a list of two arrays.
        # We typically use the SHAP values for the positive class (index 1).
        if isinstance(shap_values, list) and len(shap_values) == 2:
            shap_values = shap_values[1]

        return shap_values

    @staticmethod
    def get_sorted_features_by_importance(
        shap_values, x_train: DataFrame
    ) -> List[Feature]:
        """
        Get the sorted features by importance based on the SHAP values.
        """
        mean_shap_values = np.abs(shap_values).mean(axis=0)
        sorted_indices = mean_shap_values.argsort()[::-1]
        return x_train.columns[sorted_indices].tolist()

    @staticmethod
    def display_beeswarm_plot(shap_values, x_train):
        """
        Display a beeswarm plot of the SHAP values.
        """
        return summary_plot(shap_values, x_train.astype("float"))
