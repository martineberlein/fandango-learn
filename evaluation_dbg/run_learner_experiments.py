from evaluation_dbg.learner.experiments import (
    get_calculator_experiment,
    get_heartbleed_experiment,
    get_middle_experiment,
    get_expression_experiment,
    get_markup1_experiment,
    get_markup2_experiment,
    get_pysnooper1_experiment,
    get_pysnooper2_experiment,
    get_cookiecutter1_experiment,
    get_cookiecutter2_experiment,
)
from evaluation_dbg.util import get_log_file_name, write_log_header, row_print_averages, average_results, get_csv_file_name
import random

from dbg.logger import LoggerLevel
from dbg_evaluation.util import save_results_to_csv


def evaluate_calculator(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_calculator_experiment().evaluate(seed=random_seed)


def evaluate_heartbleed(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_heartbleed_experiment().evaluate(seed=random_seed)


def evaluate_middle(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_middle_experiment().evaluate(seed=random_seed)


def evaluate_expression(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_expression_experiment().evaluate(seed=random_seed)


def evaluate_markup1(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_markup1_experiment().evaluate(seed=random_seed)


def evaluate_markup2(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_markup2_experiment().evaluate(seed=random_seed)


def evaluate_pysnooper1(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_pysnooper1_experiment().evaluate(seed=random_seed)


def evaluate_pysnooper2(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_pysnooper2_experiment().evaluate(seed=random_seed)


def evaluate_cookiecutter1(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_cookiecutter1_experiment().evaluate(seed=random_seed)


def evaluate_cookiecutter2(logger_level=LoggerLevel.CRITICAL, random_seed=1):
    return get_cookiecutter2_experiment().evaluate(seed=random_seed)


def run_evaluation(seconds: int = 3600, write_to_file: bool = True):
    seeds = [1, 2,3,4,5]
    experiment_name = "learner"
    log_file = get_log_file_name(experiment_name)
    csv_file = get_csv_file_name(experiment_name)
    if write_to_file:
        write_log_header(log_file)

    experiments = [
        evaluate_calculator,
        evaluate_heartbleed,
        evaluate_middle,
        # evaluate_expression,
        evaluate_markup1,
        evaluate_markup2,
        evaluate_pysnooper1,
        evaluate_pysnooper2,
        # evaluate_cookiecutter1,
        # evaluate_cookiecutter2,
    ]

    for experiment in experiments:
        results_list = []
        for seed in seeds:
            random.seed(seed)
            results = experiment(logger_level=LoggerLevel.CRITICAL, random_seed=seed)
            results_list.append(results)

        if write_to_file:
            save_results_to_csv(results_list, csv_file)

        avg_results = average_results(results_list)
        row_print_averages(avg_results, log_file, write_to_file)


if __name__ == "__main__":
    run_evaluation(write_to_file=True)