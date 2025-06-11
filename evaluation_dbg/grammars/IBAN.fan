<start> ::= <iban>;
<iban> ::= <country><checksum><bban>;
<country> ::= "DE" | "AT" | "CH" | "ES" | "FR" | "IT" | "NL" | "BE" | "LU" | "GB";
<checksum> ::= <digit><digit>;
<bban> ::= <number>;
<number> ::= <digit><number>
           | <digit>;
<digit>::=  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";