<start> ::= <arithexp>+;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;

#forall <container> in <start>:
    exists <elem> in <arithexp>:
        (len(str(<elem>.<function>)) == 4);
