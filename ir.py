from dataclasses import dataclass
from enum import Enum, auto
from weakref import proxy

class OpEnum(Enum):
    ASSIGN = auto()
    RETURN = auto()
    ADD = auto()
    MUL = auto()

class Instruction:
    __slots__ = "op", "args"
    def __init__(self, op: OpEnum, *args):
        self.op = op
        self.args = args
    
    def __str__(self):
        gen = (f"%{arg.name}" if isinstance(arg, Function) else str(arg) for arg in self.args)
        return f"   {self.op.name} " + ", ".join(gen)

class Type:
    def __eq__(self, other):
        return isinstance(other, Type) and self.__class__ == other.__class__
    
    __str__ = lambda self: self.__class__.__name__
    __repr__ = lambda self: self.__class__.__name__

class PointerType(Type):
    def __init__(self, typ):
        self.to = typ

    def __eq__(self, other):
        return isinstance(other, Pointer) and self.to == other.to

class IntType(Type):
    pass

class FuncType(Type):
    def __init__(self, ret, args):
        self.ret = ret
        self.args = args
    
    __hash__ = lambda self: hash(self.name)

    def __str__(self):
        return "(" + ", ".join(str(arg) for arg in self.args) + f") -> {self.ret}" 

class Value:
    def __init__(self, name, typ, val=None):
        self.name = name
        self.type = typ
        self.val = val

    ref = lambda self: self

    __hash__ = lambda self: hash(self.name)
    __str__ = lambda self: f"%{self.name}" if self.val is None else f"Const({self.val})"

class SymbolTable:
    __slots__ = ("symbols",)
    def __init__(self):
        self.symbols = dict()
    
    __str__ = lambda self: '\n'.join(str(symbol) for symbol in self.symbols.values())
    __contains__ = lambda self, lhs: lhs in self.symbols
    __iter__ = lambda self: (symbol for symbol in self.symbols.values())
    
    def insert(self, val):
        if val in self.symbols:
            raise KeyError(f"{val.name} is already in symbol table")
        self.symbols[hash(val)] = val
        return val

    def lookup(self, name):
        return self.symbols[hash(name)]
    

class BasicBlockBuilder:
    def __init__(self, block_ref):
        self.block_ref = block_ref

    __enter__ = lambda self: self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass
    
    def value(self, typ, const):
        return self.block_ref.func_ref.make_value(typ, None, const)

    def build_ret(self, val):
        self.block_ref.block.append(Instruction(OpEnum.RETURN, val))

    def build_add(self, typ, lhs, rhs):
        returned = self.block_ref.func_ref.make_value(typ)
        self.block_ref.block.append(Instruction(OpEnum.ADD, returned, lhs, rhs))
        return returned

    def build_mul(self, typ, lhs, rhs):
        returned = self.block_ref.func_ref.make_value(typ)
        self.block_ref.block.append(Instruction(OpEnum.MUL, returned, lhs, rhs))
        return returned

class BasicBlock:
    def __init__(self, func_ref):
        self.func_ref = func_ref
        self.block = list()

    def __str__(self):
        return '\n'.join(str(i) for i in self.block) + '\n'
    
    __len__ = lambda self: len(self.block)
    
    def builder(self):
        return BasicBlockBuilder(proxy(self))

class Function:
    def __init__(self, name, typ):
        self.name = name
        self.type = typ
        self.next_uid = 0
        self.symbol_table = SymbolTable()
        self.blocks = list()

        for name, typ in self.type.args:
            print(type(name), type(typ))
            val = Value(name, typ)
            self.symbol_table.insert(val)

    __hash__ = lambda self: hash(self.name)

    def __str__(self):
        s = f"%{self.name}: {str(self.type)}\n"
        for idx, block in enumerate(self.blocks):
            s += f"{idx}:\n" + str(block)
        return s + '\n'

    def add_BasicBlock(self, loc=None):
        block = BasicBlock(proxy(self))
        loc = len(self.blocks) if loc is None else loc
        self.blocks.insert(loc, block)
        return block

    def make_value(self, typ, name=None, const=None):
        if name is not None:
            return self.symbol_table.insert(Value(name, typ, const))
        
        while True:
            uid = str(self.next_uid)
            self.next_uid += 1

            if uid not in self.symbol_table:
                return self.symbol_table.insert(Value(uid, typ))

    def get_value(self, name):
        return self.symbol_table.lookup(name)

class Module:
    def __init__(self, name):
        self.name = name
        self.symbol_table = SymbolTable()

    __str__ = lambda self: f"module {self.name}:\n" + str(self.symbol_table)

    insert = lambda self, symbol: self.symbol_table.insert(symbol)

    def make_value(self, typ, name, val=None):
        return self.symbol_table.insert(Value(typ, name, val))

    def get_value(self, name):
        return self.symbol_table.lookup(name)

if __name__ == "__main__":

    main_module = Module("main")
    
    bar = main_module.make_value("bar", IntType(), 69)
    
    func = main_module.insert(
        Function(
            "foo",
            FuncType(
                IntType(), 
                []
            )
        )
    )

    with func.add_BasicBlock().builder() as b:
        b.build_ret(main_module.get_value("foo"))

    print(main_module)

