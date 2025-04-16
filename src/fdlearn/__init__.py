#!/usr/bin/env python3
from fandango.language.tree import DerivationTree

__version__ = "0.9.1"


def __contains__(self, other) -> bool:
    if isinstance(other, DerivationTree):
        if self.find_all_nodes(other.symbol):
            return True
        return False
    return other in self.value()


DerivationTree.__contains__ = __contains__