# Project Improvements: Fandango-Learn

This document outlines identified bugs, performance bottlenecks, and structural improvements for the Fandango-Learn (Matador) codebase.

## 1. Critical Runtime Bugs

*   **Multiprocessing Engine Crash:** `ProcessBasedParallelEngine` passes a `Manager().list()` to workers, but the workers attempt to call `.put()` (a `Queue` method) instead of `.append()`. This causes an `AttributeError` in parallel execution.
*   **None-Type Slicing in Refinement:** `FandangoRefinement.learn_candidates` attempts to slice the result of `get_best_candidates()`, which can return `None` if no candidates meet the criteria, leading to a `TypeError`.
*   **Unsafe Default Arguments:** In `mutation.py`, `ReplaceFragmentOperator.replace` uses the built-in `dict` type as a default argument value, which leads to `TypeError` when calling `.get()` on the class descriptor instead of an instance.
*   **State Leakage in Learner:** `FandangoLearner` does not override the `reset()` method to clear its specific state (e.g., `all_positive_inputs`, `removed_candidates`), causing data to leak between subsequent learning runs.

## 2. Performance Bottlenecks

*   **Candidate Evaluation Loop:** `FandangoConstraintCandidate` uses a Python dictionary to cache results for every input. For large datasets, the overhead of dictionary lookups and manual loops in conjunctions/disjunctions is massive.
    *   *Improvement:* Use `numpy` boolean arrays or bitmasks for O(1) vectorized logical operations.
*   **Expensive Feature Evaluation:** `DerivationFeature.evaluate` falls back to a full grammar parse of subtrees when simple checks fail. Re-parsing strings into trees during every feature check is extremely slow.
    *   *Improvement:* Implement a structural tree-matching visitor to check derivations without converting to strings.
*   **Manual Process Management:** The `Engine` classes manually manage lists of `Process` and `Thread` objects, which is prone to zombie processes and deadlocks.
    *   *Improvement:* Migrate to `concurrent.futures.ProcessPoolExecutor`.

## 3. Architectural & Pattern Instantiation Improvements

*   **Bottom-Up (Data-Driven) Instantiation:** Currently, the system generates all theoretical combinations of variables and values (Top-Down).
    *   *Improvement:* Bind placeholders by querying the positive input trees first to see what values/non-terminals actually exist in those positions.
*   **Strict Type/Grammar Pruning:** Many instantiated patterns are nonsensical (e.g., comparing a string-only non-terminal to an integer).
    *   *Improvement:* Use `ValueMap` and `ReachabilityMap` to filter relevant non-terminals *before* performing the Cartesian product in `itertools.product`.
*   **Combinatorial Explosion in Placeholders:** The Cartesian product of `<NON_TERMINAL>` and `<ATTRIBUTE>` placeholders generates an exponential number of candidates.
    *   *Improvement:* Use Python generators (`yield`) for lazy instantiation and apply "Early Pruning" by testing candidates against a mini-batch of inputs before full validation.
*   **Attribute Search Capping:** Recursive shortest-path searches for `<ATTRIBUTE>` can explode in complex grammars.
    *   *Improvement:* Impose a strict maximum on the number of generated paths and descendant levels.

## 4. Technical Debt

*   **Unsafe `eval()`:** The use of `eval()` in `value_transformer.py` is a security risk and performance sink.
    *   *Improvement:* Replace with `ast.literal_eval` or a dedicated safe math parser.
*   **Logging vs. Print:** Multiple files contain explicit `print()` statements that bypass the `LOGGER` configuration, cluttering standard output.
