<start> ::= <arithexp>;
<arithexp> ::= <function>"("<number>")";
<function> ::= "sqrt" | "cos" | "sin" | "tan";
<number> ::= <maybeminus><onenine><maybedigits> | "0";
<maybeminus> ::= "-" | "";
<onenine> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits> ::= <digit>*;
<digit>::=  "0" | <onenine>;

#forall <container> in <start>:
#    exists <elem> in <arithexp>:
#        (len(str(<elem>.<function>)) == 4);

#exists <elem> in <maybeminus>:
#    (str(<elem>) == '-');


#forall <container_1> in <function>:
#    forall <container_2> in <number>:
#        str(<container_1>) == 'sqrt' and int(<container_2>) <= -1;

#forall <container_1> in <function>:
#    str(<container_1>) == 'sqrt';

#forall <container_2> in <number>:
#    int(<container_2>) <= -1;

#str(<function>) == 'sqrt' and int(<number>) <= -1;

(forall <container_key_1> in <function>: str(<container_key_1>) == 'sqrt') and (forall <container_key_2> in <number>: int(<container_key_2>) <= -1);

# forall <variable> in <number>: int(<variable>.<digit>) <= 5;