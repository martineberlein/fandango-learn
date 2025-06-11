<start> ::= <iban>;
<iban> ::= <country><checksum><bban>;
<country> ::= "DE" | "AT" | "CH" | "ES" | "FR" | "IT" | "NL" | "BE" | "LU" | "GB";
<checksum> ::= <digit><digit>;
<bban> ::= <number>;
<number> ::= <digit><number>
           | <digit>;
<digit>::=  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9";


def iban_checksum(iban: str) -> str:
    country = iban[:2]
    bban = iban[4:]
    moved = bban + country + "00"
    numeric = "".join(str(int(ch, 36)) for ch in moved)
    remainder = int(numeric) % 97
    return 98 - remainder

where iban_checksum(str(<iban>)) == int(<checksum>);