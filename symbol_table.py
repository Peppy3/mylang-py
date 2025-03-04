
class Symbol:
    __slots__ = "name", "val"
    def __init__(self, name, val):
        self.name = name
        self.val = val

    def __hash__(self):
        return hash(self.name)

class SymbolTable:
    __slots__ = ("symbols",)
    def __init__(self, start_list=None):
        if start_list is None:
            self.symbols = dict()
            return
        self.symbols = {name: val for name, val in start_list}
    
    __str__ = lambda self: '\n'.join(str(symbol) for symbol in self.symbols.values())
    __contains__ = lambda self, lhs: lhs in self.symbols
    __iter__ = lambda self: (symbol for symbol in self.symbols.values())
    
    def insert(self, name, val):
        if name in self.symbols:
            raise KeyError(f"{val.name} is already in symbol table")
        self.symbols[name] = val
        return val

    def get(self, name):
        val = self.symbols.get(name)
        return name, val


