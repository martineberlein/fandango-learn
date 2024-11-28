# fandango-learn

This repository contains the code for the Fandango Learn project.
The goal is to automatically learn _fandango_ constraints form a set of inputs.

## First Ideas

- Use Pattern Based Approach
   - Will likely lead to combinatorial explosion
   - Requires similar ideas as scatched in the avicenna paper, i.e. reduce the number of relevant non-terminals
- Build atomic constraints
   - Use the atomic constraints to build more complex constraints
   - Atomic constraints will be combined to more complex constraints with conjunctions and disjunctions.
- Implement different filter mechanisms 
   - Allow to rank constraints based on different criteria like precision, recall, etc.

