# fandango-learn

This repository contains the code for the Fandango Learn project.
The goal is to automatically learn _fandango_ constraints form a set of inputs.

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

## Anticipated Usage

```python
from fandango_learn import FandangoLearn

# failing + passing inputs
test_inputs = load_test_inputs() 


learner = FandangoLearn(grammar, test_inputs)
constraints = learner.learn_constraints()

for constraint in constraints:
    print(constraint)
```