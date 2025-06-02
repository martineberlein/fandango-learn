<start> ::= <content>
<content> ::= <text> | <html>
<html> ::= <open_tag> <content> <close_tag> | <self_closing_tag>
<open_tag> ::= <o> <tag_name> <attributes> <c>
<o> ::= r'<' # '<'
<c> ::= r'>' # '>'
<attributes> ::= <attribute>*
<attribute> ::= ' ' <attribute_name> '=' '"' <attribute_value> '"'
<attribute_name> ::= 'id' | 'class' | 'style'
<attribute_value> ::= <char>+
<close_tag> ::= <o> r'/' <tag_name> <c>
<self_closing_tag> ::= <o> <tag_name> r'/' <c>
<tag_name> ::= 'html' | 'head' | 'body' | 'title' | 'p' | 'h1' | 'h2' | 'h3'
<text> ::= (<char> | <special>)+
<char>::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z" | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" | "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<special> ::= " " | "!" | "\"" | "#" | "$" | "%" | "&" | "'" | "(" | ")" | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | "=" | "?" | "@" | "[" | "\\" | "]" | "_" | "`" | "{" | "|" | "}" | "~"
