<start> ::= <heartbeatrequest>;
<heartbeatrequest> ::= "\x01 "<payloadlength>" "<payload>" "<padding>;
<payloadlength>::= <onenine><maybedigits>;
<onenine>::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<maybedigits>::= "" | <digits>;
<digits>::= <digit> | <digit><digits>;
<digit>::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<payload>::= <char>+;
<padding>::= <char>*;
<char> ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" ;

# int(<payloadlength>) == len(str(<payload>));
# int(<payloadlength>) == 10;
