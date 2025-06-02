from fdlearn.learner import FandangoLearner, NonTerminal, FandangoInput
from fdlearn.interface.fandango import parse_contents


grammar = """
<start> ::= <arithexp>;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;
"""


if __name__ == "__main__":
    grammar, _ = parse_contents(grammar)

    initial_inputs = {
        ("sqrt(-900)", True),
        ("sqrt(-10)", True),
        ("sqrt(0)", False),
        ("sin(-900)", False),
        ("sqrt(2)", False),
        ("cos(10)", False),
    }
    initial_inputs = {
        FandangoInput.from_str(grammar, inp, oracle) for inp, oracle in initial_inputs
    }

    relevant_non_terminals = {
        NonTerminal("<number>"),
        NonTerminal("<maybeminus>"),
        NonTerminal("<function>"),
    }

    learner = FandangoLearner(grammar)
    learned_constraints = learner.learn_constraints(
        initial_inputs, relevant_non_terminals=relevant_non_terminals
    )

    for constraint in learner.get_best_candidates():
        print(constraint)
