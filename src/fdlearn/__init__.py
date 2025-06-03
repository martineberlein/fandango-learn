#!/usr/bin/env python3
import sys

from fandango.language.tree import DerivationTree
import fandango.logger

__version__ = "0.9.1"


def __contains__(self, other) -> bool:
    if isinstance(other, DerivationTree):
        if self.find_all_nodes(other.symbol):
            return True
        return False
    return other in self.value()

DerivationTree.__contains__ = __contains__

def silence(self, *args, **kwargs):
    """
    Silence the fandango logger.
    """
    pass

original = fandango.logger.print_exception

for module in list(sys.modules.values()):
    if not hasattr(module, "__dict__"):
        continue
    for name, obj in vars(module).items():
        if obj is original:
            setattr(module, name, silence)