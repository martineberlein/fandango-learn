<start> ::= <arithexp>;
<arithexp> ::= <term> | <number> | "(" <arithexp> ")";
<term> ::= <arithexp><operator><rarithexp>;
<rarithexp> ::= <arithexp>;
<operator> ::= " + " | " - " | " * " | " / ";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "~ " | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;

where any(str(<elem>.<operator>) == ' / ' and int(eval(str(<elem>.<rarithexp>))) == 0 for <elem> in *<term>)