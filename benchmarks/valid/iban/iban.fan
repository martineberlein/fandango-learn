<start> ::= <country><checksum><bban>;
# <country> ::= "DE" | "AT" | "CH" | "ES" | "FR" | "IT" | "NL" | "BE" | "LU" | "GB";
<country> ::= "DE" | "AT" | "CH" | "FR";
<checksum> ::= <digit><digit>;
<bban> ::= <number>;
<number> ::= <digit>{15,19};
<digit>::=  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";