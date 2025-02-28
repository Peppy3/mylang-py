from enum import Enum, auto
from weakref import proxy


#
# Explanation:
# 
# The IR consists of blocks.
# A block can has blocks and values in its symbol table.
# Yes, blocks are also treated as values
# Child blocks can reference it's parent block directly
#

class OpEnum(Enum):
    MOVE = auto()
    RETURN = auto()
    CALL = auto()
    MEMBER_ACCESS = auto()
    ADD = auto()
    MUL = auto()


class Instruction:
    __slots__ = "op", "args"
    def __init__(self, op: OpEnum, *args):
        self.op = op
        self.args = args
    
    def dissasemble(self):
        gen = (arg.dissasemble() if isinstance(arg, Block) else str(arg) for arg in self.args)
        return f"{self.op.name} " + ", ".join(gen)


class Type:
    __slots__ = ("token",)
    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return isinstance(other, Type) and self.__class__ == other.__class__
    
    __repr__ = lambda self: self.__class__.__name__


class PointerType(Type):
    __slots__ = ("to",)
    def __init__(self, token, to):
        super().__init__(token)
        self.to = to
    __str__ = lambda self: f"*{str(self.to)}"
    __eq__ = lambda self, other: isinstance(other, Pointer) and self.to == other.to

class ModuleType(Type):
    def __init__(self, token):
        super().__init__(token)

class BlockType(Type):
    def __init__(self, token):
        super().__init__(token)

class TypeType(Type):
    def __init__(self, token):
        super().__init__(token)

class BoolType(Type):
    def __init__(self, token):
        super().__init__(token)

class VoidType(Type):
    def __init__(self, token):
        super().__init__(token)

class StructType(Type):
    def __init__(self, token):
        super().__init__(token)
    
    __str__ = lambda self: "struct"

class IntType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"i{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, IntType) and self.bit_length == other.bit_length

class UintType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"u{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, UintType) and self.bit_length == other.bit_length

class FloatType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"f{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, FloatType) and self.bit_length == other.bit_length

class FuncType(Type):
    def __init__(self, ret, args):
        self.ret = ret
        self.args = args

    def __repr__(self):
        gen = (arg.name if isinstance(arg, Block) else str(arg) for arg in self.args)
        return "(" + ", ".join(gen) + f") -> {self.ret}" 

class SliceType(Type):
    __slots__ = "len", "type"
    def __init__(self, token, typ, length):
        super().__init__(token)
        self.type = typ
        self.len = length

    __str__ = lambda self: f"{str(self.type)}[{self.len}]"

class Value:
    __slots__ = "token", "type", "name"
    def __init__(self, token, name, typ):
        self.token = token
        self.type = typ
        self.name = name

    ref = lambda self: self

    __hash__ = lambda self: hash(self.name)
    __str__ = lambda self: f"%{self.name} {self.type}"

class Constant(Type):
    __slots__ = "token", "type", "const"
    def __init__(self, token, typ, const):
        self.token = token
        self.type = typ
        self.const = const

    __repr__ = lambda self: str(self.const)

class SymbolTable:
    __slots__ = ("symbols",)
    def __init__(self, start_list=None):
        if start_list is None:
            self.symbols = dict()
            return
        self.symbols = {hash(val): val for val in start_list}
    
    __str__ = lambda self: '\n'.join(str(symbol) for symbol in self.symbols.values())
    __contains__ = lambda self, lhs: lhs in self.symbols
    __iter__ = lambda self: (symbol for symbol in self.symbols.values())
    
    def insert(self, val):
        if val in self.symbols:
            raise KeyError(f"{val.name} is already in symbol table")
        self.symbols[hash(val)] = val
        return val

    def get(self, name):
        return self.symbols.get(hash(name))

class Block:
    def __init__(self, typ, parent_block, name):
        self.parent = parent_block
        self.name = name
        self.type = typ
        self.symbols = SymbolTable()
        self.instr_list = list()
        self.next_uid = 0

    __len__ = lambda self: len(self.instr_list)
    __hash__ = lambda self: hash(self.name)
    __str__ = lambda self: str(self.type)

    def dissasemble(self): 
        s = f"\n\n{self.name}:\n"
        s += str(self.symbols) + "\n"
        s += "\n".join(instr.dissasemble() for instr in self.instr_list)
        return s + "\n"

    def __enter__(self): 
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def gen_uid_or_name(self, name: str | None):
        if name is None:
            name = str(self.next_uid)
            self.next_uid += 1
        return name

    def value(self, token, typ, name=None):
        name = self.gen_uid_or_name(name)
        return self.symbols.insert(Value(token, name, typ))

    def block(self, typ, name=None):
        name = self.gen_uid_or_name(name)
        return self.symbols.insert(Block(typ, self, name))

    def lookup(self, name):
        if (val := self.symbols.get(name)) is not None:
            return val
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return None

    def build_move(self, typ, lhs, rhs):
        self.instr_list.append(Instruction(OpEnum.MOVE, typ, lhs, rhs))
    
    def build_ret(self, typ, val):
    	self.instr_list.append(Instruction(OpEnum.RETURN, typ, val))

    def build_call(self, typ, func_name, args: list):
    	returned = self.value(None, typ)
    	self.instr_list.append(Instruction(OpEnum.CALL, returned, func_name, args))
    	return returned

    def build_member_access(self, typ, struct, member):
    	returned = self.value(None, typ)
    	self.instr_list.append(Instruction(OpEnum.MEMBER_ACCESS, returned, struct, member))
    	return returned

    def build_add(self, typ, lhs, rhs):
    	returned = self.value(None, typ)
    	self.instr_list.append(Instruction(OpEnum.ADD, returned, typ, lhs, rhs))
    	return returned

    def build_mul(self, typ, lhs, rhs):
    	returned = self.value(None, typ)
    	self.instr_list.append(Instruction(OpEnum.MUL, returned, typ, lhs, rhs))
    	return returned


if __name__ == "__main__":

    main_module = Block(None)

    val1 = main_module.build_add(Constant(None, IntType(None), 42), Constant(None, IntType(None), 27))
    main_module.build_ret(val1)
    
    print(main_module)

