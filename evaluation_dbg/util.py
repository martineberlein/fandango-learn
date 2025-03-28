from typing import Dict
import subprocess
import datetime
import math


def compute_stddev(values):
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def average_results(results_list):
    total = sum(len(r['candidates']) for r in results_list)
    correct = sum(len(r['best_candidates']) for r in results_list)
    mean_length = sum(r.get('mean_length', 0) for r in results_list) / len(results_list)
    precisions = [r.get('precision', 0) for r in results_list]
    recalls = [r.get('recall', 0) for r in results_list]
    precision_mean = sum(precisions) / len(precisions)
    recall_mean = sum(recalls) / len(recalls)
    precision_stddev = compute_stddev(precisions)
    recall_stddev = compute_stddev(recalls)
    time = sum(r['time_in_seconds'] for r in results_list) / len(results_list)
    return {
        'name': results_list[0]['name'],
        'total': total // len(results_list),
        'correct': correct // len(results_list),
        'percentage': (correct / total * 100) if total > 0 else 0,
        'mean_length': mean_length,
        'precision_mean': precision_mean,
        'precision_stddev': precision_stddev,
        'recall_mean': recall_mean,
        'recall_stddev': recall_stddev,
        'time': time,
    }

def row_print_averages(results: Dict, log_file="evaluation_results.log", write_to_file: bool = True):
    header = (f"{'Subject':<15} {'Total':<6} {'Correct':<8} {'Percentage':<10} {'#Seeds':<8} "
              f"{'Mean Precision':<14} {'P-StdDev':<10} {'Mean Recall':<14} {'R-StdDev':<10} {'Time (s)':<10}")
    if not hasattr(row_print_averages, "header_printed"):
        print(header)
        print("=" * len(header))
        if write_to_file:
            with open(log_file, "a") as file:
                file.write(header + "\n" + "=" * len(header) + "\n")
        row_print_averages.header_printed = True

    row = (f"{results['name']:<15} {results['total']:<6} {results['correct']:<8} {results['percentage']:<10.2f} "
           f"{5:<8} {results['precision_mean']:<14.4f} {results['precision_stddev']:<10.4f} "
           f"{results['recall_mean']:<14.4f} {results['recall_stddev']:<10.4f} {results['time']:<10.4f}")
    print(row)
    if write_to_file:
        with open(log_file, "a") as file:
            file.write(row + "\n")


def get_log_file_name():
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H-%M-%S")
    return f"evaluation_results_{current_time}.log"

def get_csv_file_name():
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H-%M-%S")
    return f"evaluation_results_{current_time}.csv"


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


def row_print_results(results: Dict, log_file="evaluation_results.log", write_to_file: bool = True):
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

    if write_to_file:
        with open(log_file, "a") as file:
            file.write("\n".join(output) + "\n")