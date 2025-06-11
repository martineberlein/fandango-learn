<start> ::= <arithexp>;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits><maybe_frac>? | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <integer> | "";
<integer> ::= <digit><integer> | <digit>;
<maybe_frac> ::= "."<integer>;
<digit>::=  "0" | <onenine>;

where (str(<function>) == 'sqrt' and str(<maybeminus>) == '-');