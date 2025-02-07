<start> ::= <expression>;
<expression> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <minus><lead_digit><digits> | "0";
<minus> ::= "-"?;
<lead_digit> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<digits> ::= <digit>*;
<digit>::=  "0" | <lead_digit>;

str(<function>) == 'sqrt';