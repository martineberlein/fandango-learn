from dataclasses import dataclass, field


@dataclass
class Result:
    tool_name: str = ""
    subject_name: str = ""

    experiment_settings: object = None
    tool_settings: object = None

    invariants: list["ResultInvariant"] = field(default_factory=list)
    runtime: float = 0.0

    # Run successful?
    success: bool = False

    def aggregate_metrics(self) -> dict[str, float]:
        """Compute overall TP/TN/FP/FN and derived metrics."""
        total_tp = sum(inv.tp for inv in self.invariants)
        total_tn = sum(inv.tn for inv in self.invariants)
        total_fp = sum(inv.fp for inv in self.invariants)
        total_fn = sum(inv.fn for inv in self.invariants)

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0
        accuracy = (
            (total_tp + total_tn)
            / (total_tp + total_tn + total_fp + total_fn)
            if (total_tp + total_tn + total_fp + total_fn)
            else 0
        )

        return {
            "tp": total_tp,
            "tn": total_tn,
            "fp": total_fp,
            "fn": total_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
        }

    def print_summary(self):
        """Print formatted summary of result statistics."""
        if not self.success or not self.invariants:
            print(f"\nTool: {self.tool_name} | Subject: {self.subject_name}")
            print("  No successful run or no invariants.")
            return

        m = self.aggregate_metrics()
        print(f"\nTool: {self.tool_name} | Subject: {self.subject_name}")
        print(f"  Invariants: {len(self.invariants)}")
        print(f"  Runtime: {self.runtime:.2f}s")
        print(
            f"  TP={m['tp']} TN={m['tn']} FP={m['fp']} FN={m['fn']}\n"
            f"  Precision={m['precision']:.3f} Recall={m['recall']:.3f} "
            f"F1={m['f1']:.3f} Accuracy={m['accuracy']:.3f}"
        )


@dataclass
class ResultInvariant:
    invariant: object = None

    # Predictor
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0



def print_results_table(results: list[Result]):
    """Print all results as a simple table."""
    header = (
        f"{'Tool':<15} {'Subject':<25} {'Inv':>5} "
        f"{'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5} "
        f"{'Prec':>10} {'Rec':>10} {'F1':>10} {'Acc':>10} {'Time(s)':>8}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        if not r.success or not r.invariants:
            print(f"{r.tool_name:<15} {r.subject_name:<15} {'—':>5} " + " " * 60 + "No data")
            continue

        m = r.aggregate_metrics()
        print(
            f"{r.tool_name:<15} {r.subject_name:<25} {len(r.invariants):>5} "
            f"{m['tp']:>5} {m['fp']:>5} {m['tn']:>5} {m['fn']:>5} "
            f"{m['precision']:>10.3f} {m['recall']:>10.3f} {m['f1']:>10.3f} "
            f"{m['accuracy']:>10.3f} {r.runtime:>8.2f}"
        )