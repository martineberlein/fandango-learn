# fandango-learn

This repository contains the code for the Fandango Learn project.
The goal is to automatically learn _fandango_ constraints form a set of inputs.

Overall, the learner will be integrated into **Avicenna**, which provides the necessary infrastructure of the hypothesis refinement loop.
Furthermore, **Avicenna** provides the means to automatically learn the set of relevant non-terminals, reducing the search space for the learner.

## First Ideas

- Use Pattern Based Approach
   - Will likely lead to combinatorial explosion
   - Requires similar ideas as scatched in the Avicenna paper, i.e. reduce the number of relevant non-terminals
- Build atomic constraints
   - Use the atomic constraints to build more complex constraints
   - Atomic constraints will be combined to more complex constraints with conjunctions and disjunctions.
- Implement different filter mechanisms 
   - Allow to rank constraints based on different criteria like precision, recall, etc.

## Reusability

The code should be reusable for other projects, such as Avicenna.
Therefore, the code uses many abstract classes that are already implemented in Avicenna and AvicennaISLearn.
This makes comparing both approaches FandangoLearn and ISLearn extremely easy.

## Usage

Work in progress. The following code snippet shows how to use the FandangoStringPatternLearner to learn atomic constraints from a set of inputs.
See the `playground` folder for the [working prototype](./playground/working-prototype.py).

```python
from fandangoLearner.learner import FandangoStringPatternLearner
from fandango.language.parse import parse, parse_file
from fandangoLearner.input import FandangoInput, OracleResult

grammar, _ = parse_file('calculator.fan')
test_inputs = [
    ("sqrt(-900)", OracleResult.FAILING),
    ("sqrt(-10)", OracleResult.FAILING),
    ("sqrt(2)", OracleResult.PASSING),
    ("cos(-10)", OracleResult.PASSING),
    ("sin(60)", OracleResult.PASSING),
]

initial_inputs = {FandangoInput.from_str(grammar, inp, result) for inp, result in test_inputs}

patterns = [
    "int(<?NON_TERMINAL>) <= <?INTEGER>;",
    "str(<?NON_TERMINAL>) == <?STRING>;",
    "int(<?NON_TERMINAL>) == len(str(<?NON_TERMINAL>));"
]

learner = FandangoStringPatternLearner(
    grammar,
    patterns=patterns
)
filtered_candidates = learner.learn_constraints(
    initial_inputs,
    relevant_non_terminals=["<number>", "<maybeminus>", "<function>"]
)

for candidate in filtered_candidates:
    candidate.evaluate(initial_inputs)
    print("Constraint:", candidate.constraint, "Recall:", candidate.recall(), "Precision:", candidate.precision())
```

Produces the following atomic constraints (for now):

```
Constraint: int(<number>) <= -10 Recall: 1.0 Precision: 0.8
Constraint: str(<maybeminus>) == '-' Recall: 1.0 Precision: 0.8
Constraint: str(<function>) == 'sqrt' Recall: 1.0 Precision: 0.8
```

Next steps: Automatically combining constraints to more complex constraints:

```python
cand1 = filtered_candidates[-1]
cand2 = filtered_candidates[-2]
cand3 = cand1 & cand2
cand3.evaluate(initial_inputs)
print("Combined Constraints:")
print("Constraint:", cand3.constraint, "Recall:", cand3.recall(), "Precision:", cand3.precision())
```

Produces the following combined constraint:

```
Combined Constraints:
Constraint: (str(<function>) == 'sqrt' and str(<maybeminus>) == '-') Recall: 1.0 Precision: 1.0
```
