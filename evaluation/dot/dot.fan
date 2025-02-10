<start> ::= <graph>
<graph> ::= <STRICT>? <graph_type> <WS> <id_>? <WS>? "{"<WS>? <stmt_list> <WS>? "}"
<graph_type> ::= "graph" | "digraph"
<stmt_list> ::= (<stmt> <WS>? ";"? <WS>?) *
<stmt> ::= <node_stmt>
         | <edge_stmt>
         | <attr_stmt>
         | <id_> <WS>? "=" <WS>? <id_>
         | <subgraph>
<attr_stmt> ::= (<GRAPH> | <NODE> | <EDGE>) <WS>? <attr_list>
<attr_list> ::= ("[" <WS>? <a_list>? <WS>? "]") +
<a_list> ::= (<id_> <WS>? ("=" <WS>? <id_> <WS>?)? (";" | ",")? <WS>? )+
<edge_stmt> ::= (<node_id> | <subgraph>) <WS>? <edgeRHS> <attr_list>?
<edgeRHS> ::= (<edgeop> <WS>? (<node_id> | <subgraph>) <WS>? )+
<edgeop> ::= "->" | "--"
<node_stmt> ::= <node_id> <WS>? <attr_list>?
<node_id> ::= <id_> <WS>? <port>?
<port> ::= ":" <WS>? <id_> <WS>? (":"<WS>? <id_>)?
<subgraph> ::= (<SUBGRAPH> <WS>? <id_>? <WS>?)? "{"<WS>? <stmt_list> <WS>?"}"
<id_> ::= <ID> | <STRING> | <NUMBER>
<STRICT> ::= "strict" <WS>
<GRAPH> ::= "graph"
<DIGRAPH> ::= "digraph"
<NODE> ::= "node"
<EDGE> ::= "edge"
<SUBGRAPH> ::= "subgraph"
<NUMBER> ::= "-"? ("." <DIGIT>+ | <DIGIT>+ ("." <DIGIT>*)?)
<DIGIT> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" |"9"
<STRING> ::= '"' <LETTER>+ '"' | '"' '"'
<ID> ::= <ID_LETTER>+
<ID_LETTER> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j"
                  | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t"
                  | "u" | "v" | "w" | "x" | "y" | "z"
                  | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J"
                  | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T"
                  | "U" | "V" | "W" | "X" | "Y" | "Z" | "_" | "." | "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<LETTER> ::= "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j"
                  | "k" | "l" | "m" | "n" | "o" | "p" | "q" | "r" | "s" | "t"
                  | "u" | "v" | "w" | "x" | "y" | "z"
                  | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J"
                  | "K" | "L" | "M" | "N" | "O" | "P" | "Q" | "R" | "S" | "T"
                  | "U" | "V" | "W" | "X" | "Y" | "Z" | "_" | "." | "-" | "/" | ","
                   |"0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "(" | ")" | " " | "+" | "-" | "*" | "%"
<WS> ::= ( "\t" | "\n" | " " )*
