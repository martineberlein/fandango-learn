<start> ::= <options>;
<options> ::= <op>;
<op> ::= <output><depth><prefix><variables>;
<sep> ::= " " | "\n";
<output> ::= "-o"<sep>
           | "-o"<path><sep>
           | "-o"<sep><path><sep>
           | "";
<depth> ::= "-d"<number><sep>
         | "-d"<sep><number><sep>
         | "-d="<number><sep>
         | "";
<prefix> ::= "-p"<str_ascii><sep>
          | "-p"<sep><str_ascii><sep>
          | "-p="<str_ascii><sep>
          | "";
<variables> ::= "-v"<variable_list><sep>
           | "-v"<sep><variable_list><sep>
           | "-v="<variable_list><sep>
           | "";
<path> ::= <location>
        | <location>"."<str_ascii>;
<location> ::= <str_ascii>
            | <path>"/"<str_ascii>;
<variable_list> ::= <variable>
                 | <variable_list>","<variable>;
<variable> ::= <name>
            | <variable>"."<name>;
<name> ::= <letter><chars>;
<chars> ::= ""
         | <chars><char>;
<letter> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j"
                  | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t"
                  | "u" | "v" | "w" | "x" | "y" | "z"
                  | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J"
                  | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T"
                  | "U" | "V" | "W" | "X" | "Y" | "Z" ;
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" |"9";
<char> ::= <letter>
        | <digit>
        | "_";
<str_ascii> ::= <chars_ascii>;
<chars_ascii> ::= <char_ascii>
               | <char_ascii><chars_ascii>;
<char_ascii> ::= <letter> | <digit> ;
<number> ::= <non_zero><digits>;
<non_zero> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";
<digits> ::= ""
          | <digit><digits>;