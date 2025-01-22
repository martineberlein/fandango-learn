import random
from typing import Dict
import subprocess
import datetime

from evaluation.calculator.evaluate_calculator import evaluate_calculator
from evaluation.heartbleed.heartbleed import evaluate_heartbleed
from evaluation.middle.middle import evaluate_middle
from evaluation.expression.expression import evaluate_expression
from evaluation.refinement.calculator.evaluate_caluclator_refinement import evaluate_calculator_refinement
from fandangoLearner.logger import LoggerLevel


def get_log_file_name():
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H-%M-%S")
    return f"evaluation_results_{current_time}.log"


def write_log_header(log_file="evaluation_results.log"):
    # Get the current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get the current Git branch and last commit hash
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        last_commit = subprocess.check_output(["git", "log", "-1", "--format=%H"], text=True).strip()
    except Exception:
        branch = "Unknown"
        last_commit = "Unknown"

    # Write the header to the log file
    with open(log_file, "w") as file:
        file.write(f"Date: {current_time}\n")
        file.write(f"Git Branch: {branch}\n")
        file.write(f"Last Commit: {last_commit}\n")
        file.write("=" * 80 + "\n")


def row_print_results(results: Dict, log_file="evaluation_results.log"):
    header = f"{'Subject':<15} {'Total':<6} {'Correct':<8} {'Percentage':<10} {'Mean Length':<12} {'Precision':<10} {'Recall':<10} {'Time (s)':<10}"
    output = []
    if not hasattr(row_print_results, "header_printed"):
        output.append(header)
        output.append("=" * len(header))
        row_print_results.header_printed = True  # Ensure the header is added only once

    total = len(results['candidates']) if results['candidates'] else 0
    correct = len(results['best_candidates']) if results['best_candidates'] else 0
    percentage = (correct / total * 100) if total > 0 else 0
    mean_length = results.get('mean_length', 'N/A')
    precision = results.get('precision', 'N/A') if results['best_candidates'] else 0
    recall = results.get('recall', 'N/A') if results['best_candidates'] else 0
    time = results['time_in_seconds']

    row = f"{results['name']:<15} {total:<6} {correct:<8} {percentage:<10.2f} {mean_length:<12} {precision:<10.4f} {recall:<10.4f} {time:<10.4f}"
    output.append(row)

    for line in output:
        print(line)

    with open(log_file, "a") as file:
        file.write("\n".join(output) + "\n")


def run_evaluation(seconds: int = 3600, random_seed: int = 1):
    random.seed(random_seed)
    log_file = get_log_file_name()
    write_log_header(log_file)  # Write the log header

    experiments = [
        evaluate_calculator_refinement,
        evaluate_calculator,
        evaluate_heartbleed,
        evaluate_middle,
        evaluate_expression,
    ]
    for experiment in experiments:
        row_print_results(experiment(logger_level=LoggerLevel.CRITICAL), log_file)


if __name__ == "__main__":
    run_evaluation()