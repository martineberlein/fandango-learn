<start> ::= <arithexp>;
<arithexp> ::= <arithexp><operator><rarithexp> | <number> | "(" <arithexp> ")";
<rarithexp> ::= <arithexp>;
<operator> ::= " + " | " - " | " * " | " / ";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "~ " | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;