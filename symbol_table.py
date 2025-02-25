from dataclasses import dataclass

@dataclass
class Symbol:
    type: Type

class SymbolTable:
    def __init__(self):
        self.symbols = set()
    
    def insert(self, name, typ):
        self.symbols.add(Symbol(typ))

    def lookup(self, name):
        typ = scope.get(name)
        return typ.type if typ is not None else None:


class ScopedSymbolTable:
    def __init__(self, globs: dict):
        self.stack = [globs]
    
    def enter_scope(self):
        self.stack.append(dict())
    
    def exit_scope(self):
        self.stack.pop()
    
    def insert(self, name, typ):
        self.stack[-1][name] = Symbol(typ)

    def lookup(self, name):
        for scope in reversed(self.stack):
            typ = scope.get(name)
            if typ is not None:
                return typ.type
        return None

