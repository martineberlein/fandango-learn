import random
from typing import Dict

from evaluation.calculator.evaluate_calculator import evaluate_calculator
from evaluation.heartbleed.heartbleed import evaluate_heartbleed
from evaluation.middle.middle import evaluate_middle
from evaluation.expression.expression import evaluate_expression

from fandangoLearner.logger import LoggerLevel


# Return the evaluation results as a tuple of values (subject, total, valid, percentage, diversity, mean_length, median)
def better_print_results(
    results: Dict
):
    print("================================")
    print(f"{results["name"]} Evaluation Results")
    print("================================")
    print(f"Learned Constraints: {len(results["candidates"])}")
    print(f"Best Equivalent Constraints: {len(results['best_candidates'])}")
    print(f"Precision: {results["precision"]:.4f}")
    print(f"Recall: {results["recall"]:.4f}")
    print(f"Time: {results['time_in_seconds']:.4f} seconds")
    print("")
    print("")


def run_evaluation(seconds: int = 3600, random_seed: int = 1):
    # Set the random seed
    random.seed(random_seed)

    experiments = [
        evaluate_calculator,
        evaluate_heartbleed,
        evaluate_middle,
        evaluate_expression,
    ]

    for experiment in experiments:
        better_print_results(experiment(logger_level=LoggerLevel.CRITICAL))


if __name__ == "__main__":
    run_evaluation()