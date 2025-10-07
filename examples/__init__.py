def row_print_averages(
    results: tuple, log_file="evaluation_results.log", write_to_file: bool = True
):
    header = (
        f"{'Subject':<15} {'Total':<6} {'Valid':<8} {'Percentage':<10} {'Grammar coverage':<20} "
        f"{'Mean length':<14} {'Median length':<10}"
    )
    if not hasattr(row_print_averages, "header_printed"):
        print(header)
        print("=" * len(header))
        if write_to_file:
            with open(log_file, "a") as file:
                file.write(header + "\n" + "=" * len(header) + "\n")
        row_print_averages.header_printed = True

    row = (
        f"{results[0]:<15} {results[1]:<6} {results[2]:<8} {results[3]:<10.2f} "
        f"{results[4][0]:<20} {results[5]:<14.4f} {results[6]:<10} "
    )
    print(row)
    if write_to_file:
        with open(log_file, "a") as file:
            file.write(row + "\n")
